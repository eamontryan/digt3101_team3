# Real Estate Management System (REMS) 🏢

> **Course:** YU-DIGT Software Engineering  
> **Deliverable:** 2 - System Architecture (SDD)   
> **Date:** Feburary 1, 2026

## 📖 Project Overview
The **Real Estate Management System (REMS)** is a comprehensive, Java-based software solution designed to automate commercial property management for large-scale mall developments.

Large real estate companies currently face inefficiencies due to fragmented tools and manual processes, resulting in double-booked appointments and billing errors. REMS solves this by centralizing workflows—from leasing and billing to maintenance—into a unified platform.

## ✨ Key Features
REMS is designed with the following core functional modules:

### 🏪 Property & Unit Management
* **Inventory Control:** Track store size, location, rental tier, classification, and tenant purpose.
* **Multi-Mall Support:** Manage multiple mall properties with distinct inventories.
* **Smart Search:** Tenants can filter units by price, size, and availability.

### 📅 Scheduling & Leasing
* **Conflict-Free Booking:** Automated logic prevents double-booking of viewing appointments.
* **Digital Applications:** Electronic submission of rental applications with file uploads.
* **E-Leases:** Auto-generated lease agreements with electronic signature support.

### 💳 Automated Billing
* **Consolidated Invoicing:** Combines base rent, electricity, water, and waste charges into a single monthly bill.
* **Flexible Cycles:** Supports monthly, quarterly, or annual billing logic.
* **Discount Logic:** Automatically applies discounts for tenants leasing multiple units.

### 🛠️ Maintenance Portal
* **Ticket System:** Tenants can submit maintenance requests online.
* **Smart Escalation:** Emergency requests are automatically prioritized and escalated.
* **Misuse Billing:** Logic to charge tenants for maintenance caused by misuse.

## 🛠️ Technology Stack
Based on the project specifications:

* **Language:** Java
* **Database:** Relational Database (MySQL or PostgreSQL)
* **Testing:** JUnit
* **Architecture:** Layered or MVC (Model-View-Controller)
* **Frontend:** Mobile-friendly & Responsive Interface

## 🚀 Project Roadmap
The project follows an Agile development cycle divided into 5 Sprints.

| Phase | Deliverable | Deadline | Status |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **SRS & Project Plan** | Nov 23, 2025 | ✅ Completed |
| **Phase 2** | **System Architecture (SDD)** | Feb 01, 2026 | ✅ Completed |
| **Phase 3** | **Core Implementation** | Mar 22, 2026 | 🚧 In Progress |
| **Phase 4** | **Testing & QA** | Mar 22, 2026 | 🚧 In Progress |
| **Phase 5** | **Enhancements** | Summer 2026 | 📅 Planned |

## 📂 Repository Structure
This repository contains the documentation and source code for REMS.

- `docs/` - Contains the SRS, SDD, and Project Reports.
- `src/` - (Future) Java source code.
- `tests/` - (Future) JUnit test suites.
- `assets/` - Diagrams, mockups, and UI assets.

## 👥 Team 3
* **Sienna Markham** 
* **Mahjabin Mollah**
* **Eamon Ryan**

## ⚠️ Limitations
Please note the following constraints for this academic project:
* **Security:** Basic authentication only; no full production-level hardening.
* **Payments:** Integration with payment processors is simulated/mocked.
* **Utilities:** Metering data is manually input or imported via CSV, not hardware-linked.
* **Localization:** The system currently supports English only.

---
*This repository is maintained for the YU-DIGT Software Engineering Capstone.*
