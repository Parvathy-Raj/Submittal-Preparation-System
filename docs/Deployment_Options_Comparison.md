# Deployment Options Comparison

## Submittal Preparation System

Prepared for: Management Review  
Prepared by: [Your Name]  
Date: 01 July 2026

---

## 1. Purpose

This document compares the available deployment options for the Submittal Preparation System. The system is currently running locally and includes:

- React frontend web application
- Python FastAPI backend
- PostgreSQL database
- User, admin, and system admin role management
- Product and document management
- Approved template management
- Automated cover page, index, divider, and final PDF generation

The objective is to choose a suitable hosting method so employees can access the system reliably and securely.

---

## 2. Important Current Server Note

Based on the current information, the company server available now appears to be mainly a file storage server. A file storage server is normally used for shared folders and company document storage.

It may not be suitable for directly hosting this web application unless IT provides a separate deployable application server or virtual machine.

For internal deployment, IT should ideally provide:

- Linux server or Linux virtual machine
- Docker and Docker Compose support
- Sufficient CPU, RAM, and storage
- Database backup facility
- Internal network access for employees
- Optional VPN or controlled external access if required

---

## 3. Options Compared

| Option | Estimated Cost | Ease of Deployment | Control | Best Use |
|---|---:|---|---|---|
| Company Linux Server / VM | Lowest if provided internally | Medium | High | Internal company use |
| AWS EC2 Cloud Server | USD 25–50/month approx. | Medium | Very High | Long-term production/cloud access |
| Railway Cloud Platform | USD 5–25/month approx. | Easy | Medium | Quick trial/demo deployment |

---

## 4. Option 1: Company Linux Server / Virtual Machine

This option means IT provides a deployable Linux server or Linux VM within the company network. The system would run using Docker Compose on that server.

### Advantages

- Lowest recurring cost if company infrastructure is available.
- Company data remains inside the company network.
- Good for internal users.
- Better control over access, documents, and backups.
- No dependency on monthly cloud billing.

### Disadvantages

- The current file storage server may not be suitable for application deployment.
- Requires IT support for server setup, maintenance, backups, and security.
- External access requires VPN, firewall, or secure remote access configuration.
- Availability depends on company server and network uptime.

### Best suited for

Internal company use where employees access the system from office network or VPN.

---

## 5. Option 2: AWS EC2 Cloud Server

This option means deploying the application on an AWS Linux server. The frontend, backend, and PostgreSQL database can run using Docker Compose on one EC2 instance.

### Estimated Cost

Approximate monthly cost for a simple setup:

| Item | Approx. Cost |
|---|---:|
| EC2 Linux server | USD 15–35/month |
| EBS storage | USD 3–8/month |
| Public IPv4 address | Approx. USD 3.60/month |
| Data transfer | Usually low; AWS includes 100 GB/month free data transfer out |
| SSL certificate | Free using Let’s Encrypt |
| Domain | Optional, usually USD 10–15/year |

Estimated total: USD 25–50/month approximately.

If AWS RDS PostgreSQL is used separately, the cost can increase significantly. For the first production version, a PostgreSQL container on the EC2 server is a lower-cost approach.

### Advantages

- Good option for long-term production use.
- Accessible from outside the office using a secure domain.
- Suitable for remote users and multiple branches.
- More scalable than an internal file server.
- Full control over server configuration.
- Backups and monitoring can be configured professionally.

### Disadvantages

- Monthly cloud cost.
- Requires cloud/server administration.
- Security, firewall, SSL, and backups must be configured carefully.
- Costs can increase if extra AWS services are added.

### Best suited for

Production deployment where users need access from outside the office, multiple branches, or remote locations.

---

## 6. Option 3: Railway Cloud Platform

Railway is a cloud deployment platform that is easier to set up than AWS. The application would usually be deployed as separate services:

- Frontend service
- Backend API service
- PostgreSQL database service

### Estimated Cost

Railway uses usage-based pricing. Based on current pricing:

| Usage Type | Approx. Cost |
|---|---:|
| Small test deployment | USD 5–10/month |
| Normal light company usage | USD 10–25/month |
| Heavier usage/document storage | USD 25+/month |

### Advantages

- Fastest and easiest cloud deployment option.
- Good for demo or trial usage.
- Built-in database options.
- Public URL available quickly.
- Less server maintenance compared to AWS.
- Good for testing with selected users.

### Disadvantages

- Less control compared to AWS or a company server.
- Current Docker Compose setup may need adjustment.
- Costs can increase with storage, traffic, and usage.
- Not the preferred final option if the company requires full infrastructure control.

### Best suited for

Quick online testing or temporary demo deployment before final production hosting is selected.

---

## 7. Recommendation

### First Preference

Request IT to provide a low-cost deployable Linux server or Linux virtual machine.

This is the best option if the system is mainly for internal company use because it keeps company documents and data within the company network and avoids recurring cloud hosting costs.

### Second Preference

Use AWS EC2 if:

- IT cannot provide a suitable deployable server.
- Users need access from outside the office.
- Multiple branches or remote employees need access.
- The system is approved for long-term production use.

### Temporary Trial Option

Use Railway if:

- We need a quick online demo.
- We want selected users to test the system before final deployment.
- We want the fastest deployment with minimal server setup.

---

## 8. Required Confirmation from IT

Before finalizing deployment, IT should confirm:

1. Can a Linux server or Linux VM be provided for application deployment?
2. Can Docker and Docker Compose be installed?
3. What CPU, RAM, and storage can be allocated?
4. Will users access the system internally only or remotely as well?
5. Can a company domain or internal URL be assigned?
6. How will database and uploaded PDF backups be handled?
7. Who will maintain server updates, SSL, firewall, and security?

---

## 9. Final Summary

For internal company use, the recommended option is a company-provided Linux server or VM.

For external/remote access and long-term cloud production, AWS EC2 is the recommended option.

For a quick temporary online trial, Railway is the easiest option.

The existing file storage server should not be assumed suitable for deployment unless IT confirms that it can safely run application services, Docker containers, and PostgreSQL.

---

## 10. Reference Links

- AWS EC2 pricing: https://aws.amazon.com/ec2/pricing/on-demand/
- AWS EBS pricing: https://aws.amazon.com/ebs/pricing/
- AWS VPC public IPv4 pricing: https://aws.amazon.com/vpc/pricing/
- Railway pricing: https://railway.com/pricing

