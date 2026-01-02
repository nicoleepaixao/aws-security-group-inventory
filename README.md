# AWS Security Group Inventory – Multi-Account & Multi-Region Audit

<div align="center">
  
![AWS Security Groups](https://img.icons8.com/color/96/amazon-web-services.png)

## Complete Security Group Audit Across AWS Organizations

**Updated: December 2, 2025**

[![Follow @nicoleepaixao](https://img.shields.io/github/followers/nicoleepaixao?label=Follow&style=social)](https://github.com/nicoleepaixao)
[![Star this repo](https://img.shields.io/github/stars/nicoleepaixao/aws-sg-inventory?style=social)](https://github.com/nicoleepaixao/aws-sg-inventory)

</div>

---

<p align="center">
  <img src="img/aws-security-group-inventory.png" alt="sg inventory Architecture" width="1200">
</p>


## **Overview**

This project implements a comprehensive Security Group inventory for multi-account, multi-region AWS environments. The solution provides a consolidated view of critical security items including default Security Groups, SSH-enabled groups, publicly exposed SSH access, resource associations, and usage status. Results are generated in an organized Excel file with three tabs for easy auditing, remediation, and prioritization.

---

## **Important Information**

### **What This Solution Does**

| **Aspect** | **Details** |
|------------|-------------|
| **Scope** | Multi-account, multi-region Security Group audit |
| **Detection** | Default SGs, SSH rules, public exposure (0.0.0.0/0) |
| **Resource Tracking** | ENIs and EC2 instances associated with each SG |
| **Usage Analysis** | Identifies unused Security Groups |
| **Output Format** | Excel (.xlsx) with 3 organized tabs |
| **Automation** | Python script with AWS CLI profiles |

### **Why This Matters**

In distributed AWS environments with multiple accounts, it's common to find Security Groups that are:

- **Created automatically** and never reviewed
- **Left as default** even when unnecessary
- **Allowing SSH** unrestricted from the internet
- **Unused** but still present (operational waste)
- **Associated with sensitive resources** without proper governance

### **Solution Benefits**

- **Organizational Governance**: Implement security at organization level
- **Attack Surface Reduction**: Identify and remove risky configurations
- **Rapid Risk Assessment**: Quickly identify security exposures
- **Evidence-Based Remediation**: Create plans backed by data
- **Audit Support**: Support compliance, FinOps, and SRE processes

---

## **Architecture**

### **Inventory Process Flow**

<p align="center">
  <img src="img/aws-security-group-inventory.png" alt="sg inventory Architecture" width="800">
</p>

---

## **How It Works**

### **1. Multi-Account Scanning**

The script processes multiple AWS profiles defined in `~/.aws/config`:

```ini
[profile dev-account]
region = us-east-1

[profile staging-account]
region = us-east-1

[profile production-account]
region = us-east-1
```

### **2. Enabled Region Discovery**

Automatically filters regions that are:

- **Enabled** in the account
- **Do not require opt-in**, or already opted-in by the team
- **Avoiding AuthFailure** errors

### **3. Detailed Security Group Collection**

For each Security Group, the inventory captures:

| **Data Point** | **Description** |
|----------------|----------------|
| **ID and Name** | Security Group identifier and name |
| **Account/Region** | Source account and AWS region |
| **VPC** | Associated Virtual Private Cloud |
| **SSH Rules** | Relevant rules involving port 22 |
| **Public Exposure** | Whether SSH is open to 0.0.0.0/0 or ::/0 |
| **Default Status** | If it's a default Security Group |

### **4. Usage Verification**

The script identifies if the SG is being used by:

- **Elastic Network Interfaces (ENIs)**
- **EC2 Instances**
- **Other resources** using network interfaces

### **5. Risk Classification**

| **Risk Level** | **Criteria** |
|----------------|-------------|
| **Critical** | SG with SSH open to world AND in use |
| **High** | Default SG associated with instances |
| **Medium** | SG with SSH open but not used (can remove) |
| **Low** | Unused SGs (operational cleanup) |

---

## **Excel Report Structure**

### **Tab 1: default_sg**

Lists all default Security Groups across accounts and regions.

### **Tab 2: ssh_open**

Security Groups containing port 22 rules.

### **Tab 3: ssh_world**

Security Groups with SSH exposed to 0.0.0.0/0 or ::/0 (internet-facing).

### **Column Definitions**

| **Column** | **Description** |
|------------|-----------------|
| `account_profile` | AWS account/profile analyzed |
| `account_id` | AWS account ID |
| `region` | AWS region |
| `security_group_id` | Security Group ID |
| `group_name` | Security Group name |
| `vpc_id` | Associated VPC |
| `is_default` | Is default SG (True/False) |
| `has_ssh_rule` | Has SSH permission (True/False) |
| `has_ssh_open_world` | SSH open to internet (True/False) |
| `in_use` | Associated with any resource (True/False) |
| `attached_eni_count` | Number of ENIs using this SG |
| `attached_resources` | List of ENIs/instances attached |
| `ssh_rules` | Description of SSH rules found |

---

## **How to Get Started**

### **1. Clone Repository**

```bash
git clone https://github.com/nicoleepaixao/aws-sg-inventory-audit.git
cd aws-sg-inventory-audit
```

### **2. Install Dependencies**

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```text
boto3
pandas
xlsxwriter
```

### **3. Configure AWS Profiles**

Set up your AWS profiles in `~/.aws/config`:

```ini
[profile dev-account]
region = us-east-1
role_arn = arn:aws:iam::111111111111:role/SecurityAudit
source_profile = management

[profile staging-account]
region = us-east-1
role_arn = arn:aws:iam::222222222222:role/SecurityAudit
source_profile = management

[profile production-account]
region = us-east-1
role_arn = arn:aws:iam::333333333333:role/SecurityAudit
source_profile = management
```

### **4. Update Script Configuration**

Edit `sg_inventory_excel.py` to specify your profiles:

```python
PROFILES = [
    "dev-account",
    "staging-account",
    "production-account",
]
```

**Note:** Ensure profiles have EC2 read permissions (`ec2:DescribeSecurityGroups`, `ec2:DescribeNetworkInterfaces`, `ec2:DescribeInstances`).

---

## **Running the Inventory**

1. **Execute Script:**
   ```bash
   python sg_inventory_excel.py
   ```

2. **Monitor Progress:** Script will scan all configured profiles and regions

3. **Review Output:** Excel file generated with timestamp

**Example output:**
```text
security_groups_inventory_20251206T210355.xlsx
```

4. **Analyze Results:** Open Excel file and review each tab for findings

---

## **Understanding the Results**

### **Example: Default Security Groups Tab**

| account_profile | account_id | region | security_group_id | group_name | is_default | in_use | attached_eni_count | attached_resources |
|-----------------|------------|--------|-------------------|------------|------------|--------|-------------------|-------------------|
| production | 123456789012 | us-east-1 | sg-0abc123 | default | True | True | 3 | eni-0123, i-0abc456 |
| dev | 987654321098 | sa-east-1 | sg-0def456 | default | True | False | 0 | |

### **Example: SSH World Exposed Tab**

| account_profile | region | security_group_id | group_name | has_ssh_open_world | in_use | ssh_rules |
|-----------------|--------|-------------------|------------|-------------------|--------|-----------|
| production | us-east-1 | sg-0xyz789 | web-servers | True | True | 0.0.0.0/0 -> 22 |
| staging | eu-west-1 | sg-0abc123 | test-sg | True | False | ::/0 -> 22 |

### **Analysis Strategies**

- **Filter by `in_use = True` + `has_ssh_open_world = True`**: Immediate security risks
- **Filter by `is_default = True` + `in_use = True`**: Governance issues
- **Filter by `in_use = False`**: Cleanup opportunities
- **Sort by `attached_eni_count`**: Prioritize high-impact remediations

---

## **Use Cases**

| **Use Case** | **Application** |
|--------------|-----------------|
| **Security Audit** | Identify insecure configurations quickly |
| **Remediation Planning** | Know which SGs can be fixed without impact |
| **Attack Surface Reduction** | Remove obsolete or exposed Security Groups |
| **Multi-Account Governance** | Consolidated view across organization |
| **SRE/SecOps Support** | Fast analysis and data-driven decisions |
| **Compliance** | Evidence for audit and compliance reviews |

---

## **Security Best Practices**

### **Immediate Actions**

| **Priority** | **Action** | **Target** |
|--------------|-----------|------------|
| **Critical** | Remove SSH 0.0.0.0/0 rules | Groups with `has_ssh_open_world = True` and `in_use = True` |
| **High** | Replace default SGs | Groups with `is_default = True` and `in_use = True` |
| **Medium** | Delete unused SGs | Groups with `in_use = False` |
| **Low** | Document SG purpose | All groups with custom names |

### **Recommended Workflow**

1. **Identify Critical Risks**: SSH open to world + in use
2. **Create Replacement SGs**: With restricted CIDR ranges
3. **Migrate Resources**: From risky SGs to secure ones
4. **Validate Changes**: Ensure connectivity maintained
5. **Remove Old SGs**: Clean up after successful migration
6. **Document**: Update runbooks and architecture diagrams

---

## **Features**

| **Feature** | **Description** |
|-------------|-----------------|
| **Multi-Account Support** | Scan unlimited AWS accounts via profiles |
| **Multi-Region Coverage** | Automatic region discovery and scanning |
| **SSH Detection** | Identify all SSH rules (port 22) |
| **Public Exposure Check** | Flag 0.0.0.0/0 and ::/0 CIDR blocks |
| **Default SG Tracking** | Find all default Security Groups |
| **Usage Analysis** | Determine if SG is attached to resources |
| **ENI Association** | Count and list network interfaces |
| **EC2 Instance Tracking** | Identify instances using each SG |
| **Excel Export** | Three organized tabs for easy analysis |
| **Timestamp Naming** | Unique file names for version control |

---

## **Technologies Used**

| **Technology** | **Version** | **Purpose** |
|----------------|-------------|-------------|
| Python | 3.8+ | Core scripting language |
| boto3 | Latest | AWS SDK for EC2 API calls |
| pandas | Latest | Data manipulation and organization |
| xlsxwriter | Latest | Excel file generation |
| AWS CLI | Latest | Profile and credential management |

---

## **Project Structure**

```text
aws-sg-inventory-audit/
│
├── README.md                          # Complete project documentation
│
├── sg_inventory_excel.py              # Main inventory script
│
├── requirements.txt                   # Python dependencies
│
└── .gitignore                         # Ignored files (*.xlsx, venv/)
```

---

## **Additional Information**

For more details about AWS Security Groups, VPC security, and best practices, refer to:

- [AWS Security Groups Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html) - Official guide
- [VPC Security Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html) - Security recommendations
- [EC2 Security Group Rules](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules.html) - Rule configuration
- [AWS Security Hub](https://aws.amazon.com/security-hub/) - Automated security checks

---

## **Future Enhancements**

| **Feature** | **Description** | **Status** |
|-------------|-----------------|------------|
| CSV Export | Additional export format option | Planned |
| Dashboard Integration | PowerBI/Grafana visualization | In Development |
| Protocol Validation | Check RDP, HTTPS, database ports | Planned |
| Auto-Remediation | Suggest fixes with Terraform/CLI | Future |
| Duplicate Detection | Find redundant Security Groups | Planned |
| Security Hub Integration | Feed findings to AWS Security Hub | Future |
| IAM Access Analyzer | Cross-reference with IAM permissions | Future |

---

## **Connect & Follow**

Stay updated with AWS security automation and best practices:

<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nicoleepaixao)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white&style=for-the-badge)](https://www.linkedin.com/in/nicolepaixao/)
[![Medium](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@nicoleepaixao)

</div>

---

## **Disclaimer**

This tool performs read-only operations and does not modify any AWS resources. Security Group configurations, AWS service behavior, and best practices may evolve over time. Always validate findings in non-production environments before implementing changes to production Security Groups. Consult official AWS documentation and your organization's security policies.

---

<div align="center">

**Happy securing your AWS infrastructure!**

*Document last updated: December 2, 2025*

</div>