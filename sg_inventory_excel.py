#!/usr/bin/env python3
"""
AWS Security Group Inventory – Multi-account, multi-region audit.

This script:
- Scans multiple AWS accounts (via local AWS profiles)
- Lists all Security Groups in all enabled regions
- Detects:
    * Default Security Groups
    * Any rule involving SSH (port 22)
    * SSH exposure to the world (0.0.0.0/0 or ::/0)
- Maps which ENIs (and EC2 instances, when applicable) are using each SG
- Generates an Excel file with three sheets:
    * default_sg  -> default Security Groups
    * ssh_open    -> SGs with SSH-related rules
    * ssh_world   -> SGs with SSH exposed to the world

Requirements:
    pip install boto3 pandas xlsxwriter
"""

import boto3
import pandas as pd
from datetime import datetime
from botocore.exceptions import ClientError, ProfileNotFound

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# List of local AWS profiles to scan.
# Replace these names with the profiles you have configured in ~/.aws/config
PROFILES = [
    "account-profile-1",
    "account-profile-2",
    "account-profile-3",
    # Add more profiles as needed
]

# Output Excel filename (timestamped)
OUTPUT_FILE = f"security_groups_inventory_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.xlsx"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def get_all_regions(session):
    """
    Return only enabled/opted-in regions for the current account.
    This avoids AuthFailure errors in regions that require opt-in.
    """
    ec2 = session.client("ec2", region_name="us-east-1")
    resp = ec2.describe_regions(AllRegions=True)
    regions = []

    for r in resp["Regions"]:
        name = r["RegionName"]
        status = r.get("OptInStatus")
        # Keep regions that are either default, not requiring opt-in, or already opted-in
        if status in (None, "opt-in-not-required", "opted-in"):
            regions.append(name)

    return regions


def get_account_id(session):
    """Return the AWS Account ID for the given session."""
    sts = session.client("sts")
    return sts.get_caller_identity()["Account"]


def collect_sg_data(profile):
    """
    Collect Security Group data for a single AWS profile:
    - all SGs in all enabled regions
    - SSH rules
    - world-exposed SSH
    - ENIs and instances using each SG
    """
    print(f"\n=== Collecting Security Groups for profile: {profile} ===")

    try:
        session = boto3.Session(profile_name=profile)
    except ProfileNotFound:
        print(f"Profile {profile} not found in ~/.aws/config. Skipping.")
        return []

    account_id = get_account_id(session)
    regions = get_all_regions(session)

    rows = []

    for region in regions:
        print(f"  Region: {region}")
        ec2 = session.client("ec2", region_name=region)

        try:
            paginator = ec2.get_paginator("describe_security_groups")
            for page in paginator.paginate():
                for sg in page["SecurityGroups"]:
                    sg_id = sg["GroupId"]
                    sg_name = sg.get("GroupName", "")
                    vpc_id = sg.get("VpcId", "")
                    is_default = sg_name == "default"

                    # Flags for SSH analysis
                    has_ssh_rule = False
                    has_ssh_open_world = False
                    ssh_rules_desc = []

                    # ------------------------------------------------------------------
                    # Analyze ingress rules to detect SSH-related permissions
                    # ------------------------------------------------------------------
                    for perm in sg.get("IpPermissions", []):
                        ip_protocol = perm.get("IpProtocol")
                        from_port = perm.get("FromPort")
                        to_port = perm.get("ToPort")

                        # Check if this permission includes port 22 (SSH)
                        includes_ssh = False
                        if ip_protocol in ["tcp", "-1"]:
                            if from_port is None and to_port is None:
                                # all ports
                                includes_ssh = True
                            elif from_port is not None and to_port is not None:
                                if from_port <= 22 <= to_port:
                                    includes_ssh = True

                        if not includes_ssh:
                            continue

                        has_ssh_rule = True

                        ipv4_ranges = [r["CidrIp"] for r in perm.get("IpRanges", [])]
                        ipv6_ranges = [r["CidrIpv6"] for r in perm.get("Ipv6Ranges", [])]

                        if "0.0.0.0/0" in ipv4_ranges or "::/0" in ipv6_ranges:
                            has_ssh_open_world = True

                        rule_desc = (
                            f"protocol:{ip_protocol}, "
                            f"from:{from_port}, "
                            f"to:{to_port}, "
                            f"ipv4:{ipv4_ranges}, "
                            f"ipv6:{ipv6_ranges}"
                        )
                        ssh_rules_desc.append(rule_desc)

                    # ------------------------------------------------------------------
                    # Check if the SG is in use (ENIs + instances)
                    # ------------------------------------------------------------------
                    attached_enis = []
                    attached_instances = []
                    attached_resources_desc = []

                    try:
                        eni_paginator = ec2.get_paginator("describe_network_interfaces")
                        for eni_page in eni_paginator.paginate(
                            Filters=[{"Name": "group-id", "Values": [sg_id]}]
                        ):
                            for eni in eni_page["NetworkInterfaces"]:
                                eni_id = eni["NetworkInterfaceId"]
                                iface_type = eni.get("InterfaceType", "")
                                attachment = eni.get("Attachment", {})
                                instance_id = attachment.get("InstanceId")

                                attached_enis.append(eni_id)
                                if instance_id:
                                    attached_instances.append(instance_id)

                                desc = f"eni:{eni_id} (type:{iface_type}"
                                if instance_id:
                                    desc += f", instance:{instance_id}"
                                desc += ")"
                                attached_resources_desc.append(desc)

                    except ClientError as e:
                        print(f"    Error listing ENIs for {sg_id} in {region}: {e}")

                    in_use = len(attached_enis) > 0
                    attached_eni_count = len(attached_enis)
                    attached_resources = " | ".join(attached_resources_desc)

                    rows.append(
                        {
                            "account_profile": profile,
                            "account_id": account_id,
                            "region": region,
                            "security_group_id": sg_id,
                            "group_name": sg_name,
                            "vpc_id": vpc_id,
                            "is_default": is_default,
                            "has_ssh_rule": has_ssh_rule,
                            "has_ssh_open_world": has_ssh_open_world,
                            "ssh_rules": " | ".join(ssh_rules_desc),
                            "in_use": in_use,
                            "attached_eni_count": attached_eni_count,
                            "attached_resources": attached_resources,
                        }
                    )

        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AuthFailure":
                print(f"  Region {region} ignored (not enabled for this account).")
            else:
                print(f"  Error in {region}: {e}")

    return rows


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    all_rows = []

    for profile in PROFILES:
        rows = collect_sg_data(profile)
        all_rows.extend(rows)

    if not all_rows:
        print("No Security Groups found for the configured profiles.")
        return

    df = pd.DataFrame(all_rows)

    # Filtered views for each sheet
    df_default = df[df["is_default"] == True]
    df_ssh = df[df["has_ssh_rule"] == True]
    df_ssh_world = df[df["has_ssh_open_world"] == True]

    # Write to Excel with three sheets
    with pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter") as writer:
        df_default.to_excel(writer, sheet_name="default_sg", index=False)
        df_ssh.to_excel(writer, sheet_name="ssh_open", index=False)
        df_ssh_world.to_excel(writer, sheet_name="ssh_world", index=False)

    print(f"\nExcel file generated: {OUTPUT_FILE}")
    print("Sheets:")
    print(" - default_sg  -> default Security Groups")
    print(" - ssh_open    -> SGs with SSH-related rules")
    print(" - ssh_world   -> SGs with SSH open to 0.0.0.0/0 or ::/0")
    print("\nKey columns:")
    print(" - in_use              -> True/False, whether the SG is attached to any ENI")
    print(" - attached_eni_count  -> how many ENIs are using this SG")
    print(" - attached_resources  -> list of ENIs and instances associated")


if __name__ == "__main__":
    main()
