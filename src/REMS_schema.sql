-- ============================================================
-- Real Estate Management System (REMS) - MySQL DB Schema
-- ============================================================

DROP DATABASE IF EXISTS rems_db;
CREATE DATABASE rems_db;
USE rems_db;

-- ============================================================
-- 1. USER table (single-table inheritance for Admin, LeasingAgent, Tenant)
-- ============================================================
CREATE TABLE `user` (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    role            ENUM('Admin', 'LeasingAgent', 'Tenant') NOT NULL,
    phone           VARCHAR(20),
    status          ENUM('Active', 'Inactive', 'Suspended') NOT NULL DEFAULT 'Active',

    -- Admin-specific
    company_name          VARCHAR(150),

    -- LeasingAgent-specific
    availability_schedule VARCHAR(255),

    -- Tenant-specific
    preferred_payment_cycle ENUM('Monthly', 'Quarterly', 'Semi-Annual', 'Annual'),

    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- 2. MALL
-- ============================================================
CREATE TABLE mall (
    mall_id   INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(150) NOT NULL,
    location  VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- 3. STORE_UNIT  (composition: belongs to exactly 1 Mall)
-- ============================================================
CREATE TABLE store_unit (
    unit_id             INT AUTO_INCREMENT PRIMARY KEY,
    mall_id             INT NOT NULL,
    location            VARCHAR(100) NOT NULL,
    size                DECIMAL(10,2) NOT NULL COMMENT 'Size in square meters',
    rental_rate         DECIMAL(12,2) NOT NULL COMMENT 'Monthly rental rate',
    classification_tier VARCHAR(50),
    business_purpose    VARCHAR(150),
    availability        ENUM('Available', 'Occupied', 'Under Maintenance') NOT NULL DEFAULT 'Available',
    contact_info        VARCHAR(255),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_store_unit_mall
        FOREIGN KEY (mall_id) REFERENCES mall(mall_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 4. APPOINTMENT  (LeasingAgent 1 — 0..* Appointment, Tenant 1 — 0..* Appointment, StoreUnit 1 — 0..* Appointment)
-- ============================================================
CREATE TABLE appointment (
    appointment_id  INT AUTO_INCREMENT PRIMARY KEY,
    agent_id        INT NOT NULL,
    tenant_id       INT NOT NULL,
    unit_id         INT NOT NULL,
    date_time       DATETIME NOT NULL,
    status          ENUM('Scheduled', 'Completed', 'Cancelled', 'No-Show') NOT NULL DEFAULT 'Scheduled',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_appointment_agent
        FOREIGN KEY (agent_id) REFERENCES `user`(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_tenant
        FOREIGN KEY (tenant_id) REFERENCES `user`(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_unit
        FOREIGN KEY (unit_id) REFERENCES store_unit(unit_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 5. RENTAL_APPLICATION  (Tenant 1 — 0..* RentalApplication, StoreUnit 1 — 0..* RentalApplication)
-- ============================================================
CREATE TABLE rental_application (
    application_id   INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id        INT NOT NULL,
    unit_id          INT NOT NULL,
    submission_date  DATE NOT NULL,
    status           ENUM('Pending', 'Approved', 'Rejected', 'Withdrawn') NOT NULL DEFAULT 'Pending',
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_rental_app_tenant
        FOREIGN KEY (tenant_id) REFERENCES `user`(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rental_app_unit
        FOREIGN KEY (unit_id) REFERENCES store_unit(unit_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 6. LEASE  (Tenant 1 — 0..* Lease, StoreUnit 1 — 0..* Lease)
--    Note: A store unit can have many leases over its lifetime
--          but at most 1 active lease per store unit.
-- ============================================================
CREATE TABLE lease (
    lease_id       INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id      INT NOT NULL,
    unit_id        INT NOT NULL,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    payment_cycle  ENUM('Monthly', 'Quarterly', 'Semi-Annual', 'Annual') NOT NULL DEFAULT 'Monthly',
    status         ENUM('Active', 'Expired', 'Terminated', 'Pending') NOT NULL DEFAULT 'Pending',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_lease_tenant
        FOREIGN KEY (tenant_id) REFERENCES `user`(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_lease_unit
        FOREIGN KEY (unit_id) REFERENCES store_unit(unit_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 7. INVOICE  (Lease 1 — 1..* Invoice)
-- ============================================================
CREATE TABLE invoice (
    invoice_id    INT AUTO_INCREMENT PRIMARY KEY,
    lease_id      INT NOT NULL,
    issue_date    DATE NOT NULL,
    due_date      DATE NOT NULL,
    total_amount  DECIMAL(12,2) NOT NULL,
    status        ENUM('Pending', 'Paid', 'Overdue', 'Partially Paid', 'Cancelled') NOT NULL DEFAULT 'Pending',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_invoice_lease
        FOREIGN KEY (lease_id) REFERENCES lease(lease_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 8. PAYMENT  (Invoice 1 — 0..* Payment, aggregation)
-- ============================================================
CREATE TABLE payment (
    payment_id    INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id    INT NOT NULL,
    amount        DECIMAL(12,2) NOT NULL,
    payment_date  DATE,
    due_date      DATE NOT NULL,
    status        ENUM('Pending', 'Completed', 'Failed', 'Refunded') NOT NULL DEFAULT 'Pending',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 9. UTILITY_USAGE  (Invoice 1 — 0..* UtilityUsage)
-- ============================================================
CREATE TABLE utility_usage (
    utility_id    INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id    INT NOT NULL,
    type          VARCHAR(50) NOT NULL COMMENT 'e.g. Electricity, Water, Gas',
    usage_amount  DECIMAL(10,2) NOT NULL,
    billing_month DATE NOT NULL COMMENT 'First day of the billing month',
    amount        DECIMAL(12,2) NOT NULL COMMENT 'Billed amount',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_utility_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 10. MAINTENANCE_REQUEST  (Lease 1 — 0..* MaintenanceRequest)
-- ============================================================
CREATE TABLE maintenance_request (
    request_id   INT AUTO_INCREMENT PRIMARY KEY,
    lease_id     INT NOT NULL,
    category     VARCHAR(100) NOT NULL,
    priority     ENUM('Low', 'Medium', 'High', 'Urgent') NOT NULL DEFAULT 'Medium',
    status       ENUM('Open', 'In Progress', 'Resolved', 'Closed', 'Rejected') NOT NULL DEFAULT 'Open',
    misuse_flag  TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 = flagged as misuse',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_maintenance_lease
        FOREIGN KEY (lease_id) REFERENCES lease(lease_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_user_role       ON `user`(role);
CREATE INDEX idx_user_status     ON `user`(status);
CREATE INDEX idx_store_unit_mall ON store_unit(mall_id);
CREATE INDEX idx_store_unit_avail ON store_unit(availability);
CREATE INDEX idx_appointment_dt  ON appointment(date_time);
CREATE INDEX idx_lease_status    ON lease(status);
CREATE INDEX idx_lease_tenant    ON lease(tenant_id);
CREATE INDEX idx_lease_unit      ON lease(unit_id);
CREATE INDEX idx_invoice_status  ON invoice(status);
CREATE INDEX idx_invoice_due     ON invoice(due_date);
CREATE INDEX idx_payment_status  ON payment(status);
CREATE INDEX idx_maint_status    ON maintenance_request(status);
CREATE INDEX idx_maint_priority  ON maintenance_request(priority);
CREATE INDEX idx_utility_invoice ON utility_usage(invoice_id);
CREATE INDEX idx_rental_app_status ON rental_application(status);


-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Users: Admins
INSERT INTO `user` (username, password, name, email, role, phone, status, company_name)
VALUES
('admin_john',  'hashed_pw_001', 'John Carter',   'john.carter@rems.com',   'Admin', '09171234567', 'Active', 'REMS Holdings Inc.'),
('admin_sarah', 'hashed_pw_002', 'Sarah Mitchell','sarah.mitchell@rems.com','Admin', '09179876543', 'Active', 'REMS Holdings Inc.');

-- Users: Leasing Agents
INSERT INTO `user` (username, password, name, email, role, phone, status, company_name, availability_schedule)
VALUES
('agent_mike',  'hashed_pw_003', 'Mike Torres',   'mike.torres@rems.com',   'LeasingAgent', '09181112233', 'Active', 'REMS Holdings Inc.', 'Mon-Fri 9AM-6PM'),
('agent_lisa',  'hashed_pw_004', 'Lisa Reyes',    'lisa.reyes@rems.com',    'LeasingAgent', '09182223344', 'Active', 'REMS Holdings Inc.', 'Mon-Sat 10AM-7PM'),
('agent_david', 'hashed_pw_005', 'David Chen',    'david.chen@rems.com',    'LeasingAgent', '09183334455', 'Active', 'REMS Holdings Inc.', 'Tue-Sat 8AM-5PM');

-- Users: Tenants
INSERT INTO `user` (username, password, name, email, role, phone, status, preferred_payment_cycle)
VALUES
('tenant_anna',   'hashed_pw_006', 'Anna Lopez',     'anna.lopez@email.com',     'Tenant', '09191234567', 'Active', 'Monthly'),
('tenant_brian',  'hashed_pw_007', 'Brian Santos',    'brian.santos@email.com',   'Tenant', '09192345678', 'Active', 'Quarterly'),
('tenant_carla',  'hashed_pw_008', 'Carla Mendoza',  'carla.mendoza@email.com',  'Tenant', '09193456789', 'Active', 'Monthly'),
('tenant_derek',  'hashed_pw_009', 'Derek Villanueva','derek.villa@email.com',    'Tenant', '09194567890', 'Active', 'Semi-Annual'),
('tenant_elena',  'hashed_pw_010', 'Elena Cruz',      'elena.cruz@email.com',    'Tenant', '09195678901', 'Active', 'Annual');

-- Malls
INSERT INTO mall (name, location)
VALUES
('Greenfield Mall',    '123 Commerce Ave, Makati City'),
('Sunrise Plaza',      '456 Business Blvd, Quezon City'),
('Horizon Town Center','789 Main Street, Pasig City');

-- Store Units
INSERT INTO store_unit (mall_id, location, size, rental_rate, classification_tier, business_purpose, availability, contact_info)
VALUES
-- Greenfield Mall units
(1, 'Ground Floor, Unit G-01', 120.00, 85000.00, 'Premium',  'Retail',          'Occupied',   'leasing@greenfield.com'),
(1, 'Ground Floor, Unit G-02', 80.00,  55000.00, 'Standard', 'Food & Beverage', 'Available',  'leasing@greenfield.com'),
(1, '2nd Floor, Unit 2-01',    150.00, 95000.00, 'Premium',  'Retail',          'Occupied',   'leasing@greenfield.com'),
(1, '2nd Floor, Unit 2-02',    60.00,  40000.00, 'Economy',  'Services',        'Available',  'leasing@greenfield.com'),
(1, '3rd Floor, Unit 3-01',    200.00, 110000.00,'Anchor',   'Department Store', 'Occupied',  'leasing@greenfield.com'),
-- Sunrise Plaza units
(2, 'Ground Floor, Unit A-01', 100.00, 70000.00, 'Premium',  'Food & Beverage', 'Occupied',   'leasing@sunriseplaza.com'),
(2, 'Ground Floor, Unit A-02', 75.00,  50000.00, 'Standard', 'Retail',          'Available',  'leasing@sunriseplaza.com'),
(2, '2nd Floor, Unit B-01',    90.00,  60000.00, 'Standard', 'Services',        'Occupied',   'leasing@sunriseplaza.com'),
-- Horizon Town Center units
(3, 'Level 1, Unit L1-01',     110.00, 75000.00, 'Premium',  'Retail',          'Available',  'leasing@horizon.com'),
(3, 'Level 1, Unit L1-02',     65.00,  45000.00, 'Economy',  'Food & Beverage', 'Under Maintenance', 'leasing@horizon.com');

-- Appointments
INSERT INTO appointment (agent_id, tenant_id, unit_id, date_time, status)
VALUES
(3, 6,  2, '2026-03-10 10:00:00', 'Completed'),
(3, 7,  4, '2026-03-11 14:00:00', 'Completed'),
(4, 8,  7, '2026-03-12 11:00:00', 'Scheduled'),
(4, 9,  9, '2026-03-13 09:30:00', 'Scheduled'),
(5, 10, 2, '2026-03-15 15:00:00', 'Scheduled');

-- Rental Applications
INSERT INTO rental_application (tenant_id, unit_id, submission_date, status)
VALUES
(6,  1, '2025-11-15', 'Approved'),
(7,  3, '2025-12-01', 'Approved'),
(8,  6, '2026-01-05', 'Approved'),
(9,  8, '2026-01-20', 'Approved'),
(10, 5, '2026-02-01', 'Approved'),
(6,  2, '2026-03-10', 'Pending'),
(8,  7, '2026-03-12', 'Pending');

-- Leases
INSERT INTO lease (tenant_id, unit_id, start_date, end_date, payment_cycle, status)
VALUES
(6,  1, '2025-12-01', '2026-11-30', 'Monthly',      'Active'),
(7,  3, '2026-01-01', '2026-12-31', 'Quarterly',    'Active'),
(8,  6, '2026-02-01', '2027-01-31', 'Monthly',      'Active'),
(9,  8, '2026-02-15', '2027-02-14', 'Semi-Annual',  'Active'),
(10, 5, '2026-03-01', '2028-02-29', 'Annual',       'Active');

-- Invoices
INSERT INTO invoice (lease_id, issue_date, due_date, total_amount, status)
VALUES
-- Lease 1 (Anna, monthly)
(1, '2025-12-01', '2025-12-15', 85000.00, 'Paid'),
(1, '2026-01-01', '2026-01-15', 85000.00, 'Paid'),
(1, '2026-02-01', '2026-02-15', 85000.00, 'Paid'),
(1, '2026-03-01', '2026-03-15', 85000.00, 'Pending'),
-- Lease 2 (Brian, quarterly)
(2, '2026-01-01', '2026-01-15', 285000.00, 'Paid'),
(2, '2026-04-01', '2026-04-15', 285000.00, 'Pending'),
-- Lease 3 (Carla, monthly)
(3, '2026-02-01', '2026-02-15', 70000.00, 'Paid'),
(3, '2026-03-01', '2026-03-15', 70000.00, 'Overdue'),
-- Lease 4 (Derek, semi-annual)
(4, '2026-02-15', '2026-03-01', 360000.00, 'Paid'),
-- Lease 5 (Elena, annual)
(5, '2026-03-01', '2026-03-15', 1320000.00, 'Pending');

-- Payments
INSERT INTO payment (invoice_id, amount, payment_date, due_date, status)
VALUES
(1,  85000.00,  '2025-12-10', '2025-12-15', 'Completed'),
(2,  85000.00,  '2026-01-12', '2026-01-15', 'Completed'),
(3,  85000.00,  '2026-02-14', '2026-02-15', 'Completed'),
(5,  285000.00, '2026-01-14', '2026-01-15', 'Completed'),
(7,  70000.00,  '2026-02-13', '2026-02-15', 'Completed'),
(9,  360000.00, '2026-02-28', '2026-03-01', 'Completed'),
-- Partial payment for overdue invoice
(8,  35000.00,  '2026-03-14', '2026-03-15', 'Completed');

-- Utility Usage (linked to invoices)
INSERT INTO utility_usage (invoice_id, type, usage_amount, billing_month, amount)
VALUES
-- Invoice 1 (Anna, Dec 2025)
(1, 'Electricity', 520.00, '2025-12-01', 4800.00),
(1, 'Water',       35.00,  '2025-12-01', 1200.00),
-- Invoice 2 (Anna, Jan 2026)
(2, 'Electricity', 480.00, '2026-01-01', 4500.00),
(2, 'Water',       32.00,  '2026-01-01', 1100.00),
-- Invoice 5 (Brian, Q1 2026)
(5, 'Electricity', 780.00, '2026-01-01', 7200.00),
(5, 'Water',       50.00,  '2026-01-01', 1800.00),
-- Invoice 7 (Carla, Feb 2026)
(7, 'Electricity', 600.00, '2026-02-01', 5500.00),
(7, 'Water',       40.00,  '2026-02-01', 1400.00),
(7, 'Gas',         25.00,  '2026-02-01', 900.00),
-- Invoice 9 (Derek, Feb 2026)
(9, 'Electricity', 450.00, '2026-02-01', 4200.00),
-- Invoice 10 (Elena, Mar 2026)
(10, 'Electricity', 1200.00,'2026-03-01', 11000.00),
(10, 'Water',       90.00,  '2026-03-01', 3200.00);

-- Maintenance Requests
INSERT INTO maintenance_request (lease_id, category, priority, status, misuse_flag)
VALUES
(1, 'Plumbing',         'High',   'Resolved', 0),
(1, 'Electrical',       'Medium', 'Open',     0),
(3, 'HVAC',             'High',   'In Progress', 0),
(3, 'Pest Control',     'Low',    'Open',     0),
(4, 'Structural',       'Urgent', 'In Progress', 0),
(5, 'Cleaning',         'Low',    'Resolved', 0),
(2, 'Cosmetic Damage',  'Medium', 'Open',     1);
