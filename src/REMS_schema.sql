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
    role            ENUM('Admin', 'LeasingAgent', 'Tenant', 'Dev') NOT NULL,
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
    end_time        DATETIME NOT NULL,
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
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- Prevent double-bookings for the same agent or unit at the same time
    CONSTRAINT uq_agent_datetime  UNIQUE (agent_id, date_time),
    CONSTRAINT uq_unit_datetime   UNIQUE (unit_id, date_time)
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
    lease_id              INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id             INT NOT NULL,
    unit_id               INT NOT NULL,
    start_date            DATE NOT NULL,
    end_date              DATE NOT NULL,
    payment_cycle         ENUM('Monthly', 'Quarterly', 'Semi-Annual', 'Annual') NOT NULL DEFAULT 'Monthly',
    status                ENUM('Active', 'Expired', 'Terminated', 'Pending') NOT NULL DEFAULT 'Pending',

    -- Electronic signing
    tenant_signature      VARCHAR(255) DEFAULT NULL COMMENT 'Tenant e-signature token or hash',
    tenant_signed_at      DATETIME DEFAULT NULL,
    agent_signature       VARCHAR(255) DEFAULT NULL COMMENT 'Agent e-signature token or hash',
    agent_signed_at       DATETIME DEFAULT NULL,
    signature_status      ENUM('Unsigned', 'Partially Signed', 'Fully Signed') NOT NULL DEFAULT 'Unsigned',

    -- Lease renewal policy
    auto_renew            TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 = auto-renew enabled',
    renewal_rate_increase DECIMAL(5,2) DEFAULT NULL COMMENT 'Percentage increase on renewal e.g. 5.00 = 5%',
    renewal_status        ENUM('Not Applicable', 'Pending Renewal', 'Renewed', 'Declined') NOT NULL DEFAULT 'Not Applicable',

    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

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
    unit_id       INT NOT NULL COMMENT 'Store unit where consumption was recorded',
    invoice_id    INT DEFAULT NULL COMMENT 'NULL until consolidated into an invoice',
    type          ENUM('Electricity', 'Water', 'Waste Management') NOT NULL,
    usage_amount  DECIMAL(10,2) NOT NULL,
    billing_month DATE NOT NULL COMMENT 'First day of the billing month',
    amount        DECIMAL(12,2) NOT NULL COMMENT 'Billed amount',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_utility_unit
        FOREIGN KEY (unit_id) REFERENCES store_unit(unit_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_utility_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 10. MAINTENANCE_REQUEST  (Lease 1 — 0..* MaintenanceRequest)
-- ============================================================
CREATE TABLE maintenance_request (
    request_id    INT AUTO_INCREMENT PRIMARY KEY,
    lease_id      INT NOT NULL,
    invoice_id    INT DEFAULT NULL COMMENT 'Invoice the misuse charge was billed to',
    category      VARCHAR(100) NOT NULL,
    description   TEXT COMMENT 'Tenant description of the issue',
    priority      ENUM('Low', 'Medium', 'High', 'Urgent') NOT NULL DEFAULT 'Medium',
    status        ENUM('Open', 'In Progress', 'Resolved', 'Rejected', 'Misuse') NOT NULL DEFAULT 'Open',
    misuse_flag   TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 = flagged as misuse',
    charge_amount DECIMAL(12,2) DEFAULT NULL COMMENT 'Amount charged to tenant for misuse-related repairs',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_maintenance_lease
        FOREIGN KEY (lease_id) REFERENCES lease(lease_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_maintenance_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- 11. NOTIFICATION  (appointment confirmations, overdue alerts, etc.)
-- ============================================================
CREATE TABLE notification (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id    INT NOT NULL,
    type            ENUM('Appointment Confirmation', 'Appointment Update', 'Payment Overdue',
                         'Lease Renewal', 'Maintenance Update', 'General') NOT NULL,
    title           VARCHAR(255) NOT NULL,
    message         TEXT NOT NULL,
    related_entity  VARCHAR(50) DEFAULT NULL COMMENT 'e.g. appointment, invoice, lease',
    related_id      INT DEFAULT NULL COMMENT 'PK of the related entity',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notification_recipient
        FOREIGN KEY (recipient_id) REFERENCES `user`(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 12. APPLICATION_DOCUMENT  (file uploads for rental applications)
-- ============================================================
CREATE TABLE application_document (
    document_id    INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    file_name      VARCHAR(255) NOT NULL,
    file_path      VARCHAR(500) NOT NULL COMMENT 'Server path or object-storage URL',
    file_type      VARCHAR(50) COMMENT 'e.g. pdf, jpg, png',
    file_size      INT COMMENT 'Size in bytes',
    uploaded_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_app_doc_application
        FOREIGN KEY (application_id) REFERENCES rental_application(application_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 13. LEASE_DOCUMENT  (auto-generated lease agreements)
-- ============================================================
CREATE TABLE lease_document (
    document_id   INT AUTO_INCREMENT PRIMARY KEY,
    lease_id      INT NOT NULL,
    file_name     VARCHAR(255) NOT NULL,
    file_path     VARCHAR(500) NOT NULL COMMENT 'Server path or object-storage URL',
    generated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_lease_doc_lease
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
CREATE INDEX idx_utility_unit    ON utility_usage(unit_id);
CREATE INDEX idx_rental_app_status ON rental_application(status);
CREATE INDEX idx_notification_recipient ON notification(recipient_id);
CREATE INDEX idx_app_doc_application    ON application_document(application_id);
CREATE INDEX idx_lease_doc_lease        ON lease_document(lease_id);
CREATE INDEX idx_lease_signature        ON lease(signature_status);


-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Users: Admins
INSERT INTO `user` (username, password, name, email, role, phone, status, company_name)
VALUES
('admin_john',  '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'John Carter',   'john.carter@rems.com',   'Admin', '09171234567', 'Active', 'REMS Holdings Inc.'),
('admin_sarah', '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Sarah Mitchell','sarah.mitchell@rems.com','Admin', '09179876543', 'Active', 'REMS Holdings Inc.');

-- Users: Leasing Agents
INSERT INTO `user` (username, password, name, email, role, phone, status, company_name, availability_schedule)
VALUES
('agent_mike',  '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Mike Torres',   'mike.torres@rems.com',   'LeasingAgent', '09181112233', 'Active', 'REMS Holdings Inc.', 'Mon-Fri 9AM-6PM'),
('agent_lisa',  '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Lisa Reyes',    'lisa.reyes@rems.com',    'LeasingAgent', '09182223344', 'Active', 'REMS Holdings Inc.', 'Mon-Sat 10AM-7PM'),
('agent_david', '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'David Chen',    'david.chen@rems.com',    'LeasingAgent', '09183334455', 'Active', 'REMS Holdings Inc.', 'Tue-Sat 8AM-5PM');

-- Users: Tenants
INSERT INTO `user` (username, password, name, email, role, phone, status, preferred_payment_cycle)
VALUES
('tenant_anna',   '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Anna Lopez',      'anna.lopez@email.com',     'Tenant', '09191234567', 'Active', 'Monthly'),
('tenant_brian',  '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Brian Santos',    'brian.santos@email.com',   'Tenant', '09192345678', 'Active', 'Quarterly'),
('tenant_carla',  '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Carla Mendoza',   'carla.mendoza@email.com',  'Tenant', '09193456789', 'Active', 'Monthly'),
('tenant_derek',  '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Derek Villanueva','derek.villa@email.com',    'Tenant', '09194567890', 'Active', 'Semi-Annual'),
('tenant_elena',  '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Elena Cruz',      'elena.cruz@email.com',     'Tenant', '09195678901', 'Active', 'Annual');

-- Users: Dev (can switch between all roles)
INSERT INTO `user` (username, password, name, email, role, phone, status, company_name)
VALUES
('dev_admin', '$2b$12$uxNCjKfYzaf78GmTVYuHKev7bU3wpjwsv12CghGyBAVMrIdeK00WC', 'Dev User', 'dev@rems.com', 'Dev', '09170000000', 'Active', 'REMS Holdings Inc.');

-- Malls
INSERT INTO mall (name, location)
VALUES
('Greenfield Mall',    '123 Commerce Ave, Makati City'),
('Sunrise Plaza',      '456 Business Blvd, Quezon City'),
('Horizon Town Center','789 Main Street, Pasig City');

-- Store Units
INSERT INTO store_unit (mall_id, location, size, rental_rate, classification_tier, business_purpose, availability, contact_info)
VALUES
-- Greenfield Mall
(1, 'Ground Floor, Unit G-01', 120.00, 85000.00,  'Premium',  'Retail',           'Occupied',          'leasing@greenfield.com'),
(1, 'Ground Floor, Unit G-02', 80.00,  55000.00,  'Standard', 'Food & Beverage',  'Available',         'leasing@greenfield.com'),
(1, '2nd Floor, Unit 2-01',    150.00, 95000.00,  'Premium',  'Retail',           'Occupied',          'leasing@greenfield.com'),
(1, '2nd Floor, Unit 2-02',    60.00,  40000.00,  'Economy',  'Services',         'Available',         'leasing@greenfield.com'),
(1, '3rd Floor, Unit 3-01',    200.00, 110000.00, 'Anchor',   'Department Store',  'Occupied',         'leasing@greenfield.com'),
-- Sunrise Plaza
(2, 'Ground Floor, Unit A-01', 100.00, 70000.00,  'Premium',  'Food & Beverage',  'Occupied',          'leasing@sunriseplaza.com'),
(2, 'Ground Floor, Unit A-02', 75.00,  50000.00,  'Standard', 'Retail',           'Available',         'leasing@sunriseplaza.com'),
(2, '2nd Floor, Unit B-01',    90.00,  60000.00,  'Standard', 'Services',         'Occupied',          'leasing@sunriseplaza.com'),
-- Horizon Town Center
(3, 'Level 1, Unit L1-01',     110.00, 75000.00,  'Premium',  'Retail',           'Available',         'leasing@horizon.com'),
(3, 'Level 1, Unit L1-02',     65.00,  45000.00,  'Economy',  'Food & Beverage',  'Under Maintenance', 'leasing@horizon.com');

-- Appointments (all future-dated so they survive cleanup_past_appointments which deletes appointments in the past)
INSERT INTO appointment (agent_id, tenant_id, unit_id, date_time, end_time, status)
VALUES
(3, 6,  9, '2026-04-01 10:00:00', '2026-04-01 11:00:00', 'Scheduled'),
(3, 7,  7, '2026-04-01 14:00:00', '2026-04-01 15:00:00', 'Scheduled'), 
(4, 8,  7, '2026-04-05 11:00:00', '2026-04-05 12:00:00', 'Scheduled'), 
(4, 9,  9, '2026-04-07 09:30:00', '2026-04-07 10:30:00', 'Scheduled'), 
(5, 10, 9, '2026-04-08 15:00:00', '2026-04-08 16:00:00', 'Scheduled'); 

-- Rental Applications 
INSERT INTO rental_application (tenant_id, unit_id, submission_date, status)
VALUES
(6,  1, '2025-11-15', 'Approved'),    -- Anna → Unit G-01 (lease 1 follows)
(7,  3, '2025-12-01', 'Approved'),    -- Brian → Unit 2-01 (lease 2 follows)
(8,  6, '2025-12-05', 'Approved'),    -- Carla → Unit A-01 (lease 3 follows, shifted earlier)
(9,  8, '2026-01-20', 'Approved'),    -- Derek → Unit B-01 (lease 4 follows)
(10, 5, '2026-02-01', 'Approved'),    -- Elena → Unit 3-01 (lease 5 follows)
(6,  9, '2026-03-18', 'Pending'),     -- Anna → Unit L1-01 (Available; exploring expansion)
(8,  7, '2026-03-12', 'Pending');     -- Carla → Unit A-02 (Available; exploring expansion)

-- Leases
INSERT INTO lease (tenant_id, unit_id, start_date, end_date, payment_cycle, status,
                   tenant_signature, tenant_signed_at, agent_signature, agent_signed_at, signature_status,
                   auto_renew, renewal_rate_increase, renewal_status)
VALUES

(6,  1, '2025-12-01', '2026-11-30', 'Monthly',     'Active',
 'esign_anna_001',  '2025-11-20 14:30:00', 'esign_mike_001', '2025-11-21 09:00:00', 'Fully Signed',
 1, 5.00, 'Pending Renewal'),

(7,  3, '2026-01-01', '2026-12-31', 'Quarterly',   'Active',
 'esign_brian_001', '2025-12-15 10:00:00', 'esign_lisa_001', '2025-12-16 11:00:00', 'Fully Signed',
 0, NULL, 'Not Applicable'),

(8,  6, '2026-01-01', '2026-12-31', 'Monthly',     'Active',
 'esign_carla_001', '2025-12-18 16:00:00', 'esign_lisa_002', '2025-12-19 09:30:00', 'Fully Signed',
 1, 3.50, 'Not Applicable'),

(9,  8, '2026-02-15', '2027-02-14', 'Semi-Annual', 'Active',
 'esign_derek_001', '2026-02-01 13:00:00', 'esign_david_001','2026-02-02 10:00:00', 'Fully Signed',
 1, 4.00, 'Not Applicable'),

(10, 5, '2026-03-01', '2028-02-29', 'Annual',      'Active',
 'esign_elena_001', '2026-02-20 11:00:00', 'esign_david_002', '2026-02-21 10:00:00', 'Fully Signed',
 0, NULL, 'Not Applicable');

-- Invoices
INSERT INTO invoice (lease_id, issue_date, due_date, total_amount, status)
VALUES

(1, '2025-12-01', '2026-01-01', 91800.00,  'Paid'),     
(1, '2026-01-01', '2026-02-01', 91400.00,  'Paid'),     
(1, '2026-02-01', '2026-03-01', 85000.00,  'Paid'),     
(1, '2026-03-01', '2026-04-01', 85000.00,  'Pending'),

(2, '2026-01-01', '2026-02-01', 310000.00, 'Paid'),     
(2, '2026-04-01', '2026-05-01', 285000.00, 'Pending'),   

(3, '2026-01-01', '2026-02-01', 77800.00,  'Paid'),     
(3, '2026-02-01', '2026-03-01', 70000.00,  'Overdue'),    

(4, '2026-02-15', '2026-03-15', 364900.00, 'Paid'),   

(5, '2026-03-01', '2026-04-01', 1335700.00,'Pending');

-- Payments
INSERT INTO payment (invoice_id, amount, payment_date, due_date, status)
VALUES
(1,  91800.00,  '2025-12-20', '2026-01-01', 'Completed'),  
(2,  91400.00,  '2026-01-25', '2026-02-01', 'Completed'), 
(3,  85000.00,  '2026-02-22', '2026-03-01', 'Completed'),  
(5,  310000.00, '2026-01-28', '2026-02-01', 'Completed'), 
(7,  77800.00,  '2026-01-25', '2026-02-01', 'Completed'), 
(9,  364900.00, '2026-03-10', '2026-03-15', 'Completed'),  
(8,  35000.00,  '2026-03-10', '2026-03-01', 'Completed'); 

-- Utility Usage
INSERT INTO utility_usage (unit_id, invoice_id, type, usage_amount, billing_month, amount)
VALUES

(1, 1, 'Electricity',      520.00, '2025-12-01', 4800.00),
(1, 1, 'Water',             35.00, '2025-12-01', 1200.00),
(1, 1, 'Waste Management',   1.00, '2025-12-01',  800.00),

(1, 2, 'Electricity',      480.00, '2026-01-01', 4500.00),
(1, 2, 'Water',             32.00, '2026-01-01', 1100.00),
(1, 2, 'Waste Management',   1.00, '2026-01-01',  800.00),

(3, 5, 'Electricity',      780.00, '2026-01-01', 7200.00),
(3, 5, 'Water',             50.00, '2026-01-01', 1800.00),
(3, 5, 'Waste Management',   1.00, '2026-01-01', 1000.00),

(6, 7, 'Electricity',      600.00, '2026-01-01', 5500.00),
(6, 7, 'Water',             40.00, '2026-01-01', 1400.00),
(6, 7, 'Waste Management',   1.00, '2026-01-01',  900.00),

(8, 9, 'Electricity',      450.00, '2026-02-01', 4200.00),
(8, 9, 'Waste Management',   1.00, '2026-02-01',  700.00),

(5, 10, 'Electricity',    1200.00, '2026-03-01', 11000.00),
(5, 10, 'Water',             90.00, '2026-03-01', 3200.00),
(5, 10, 'Waste Management',   1.00, '2026-03-01', 1500.00),

(1, NULL, 'Electricity',   350.00, '2026-03-01', 3200.00),
(1, NULL, 'Water',           28.00, '2026-03-01',  950.00);

-- Maintenance Requests
INSERT INTO maintenance_request (lease_id, invoice_id, category, description, priority, status, misuse_flag, charge_amount)
VALUES
(1, NULL, 'Plumbing',        'Leaking faucet in the back storage area causing water pooling',                'High',   'Resolved',    0, NULL),
(1, NULL, 'Electrical',      'Flickering lights near the main entrance display area',                        'Medium', 'Open',        0, NULL),
(3, NULL, 'HVAC',            'Air conditioning unit not cooling properly, temperature stays above 30C',      'High',   'In Progress', 0, NULL),
(3, NULL, 'Pest Control',    'Small insects spotted near the food preparation counter',                      'Low',    'Open',        0, NULL),
(4, NULL, 'Structural',      'Crack forming on the east wall near the ceiling, possible water damage',       'Urgent', 'In Progress', 0, NULL),
(5, NULL, 'Cleaning',        'Deep cleaning requested for unit after renovation dust accumulation',          'Low',    'Resolved',    0, NULL),
(2, 5,    'Cosmetic Damage', 'Tenant caused scratches and dents on storefront glass panel and door frame',   'Medium', 'Resolved',    1, 15000.00);

-- Notifications
INSERT INTO notification (recipient_id, type, title, message, related_entity, related_id)
VALUES
(6,  'Appointment Confirmation', 'Appointment Confirmed',        'Your viewing appointment for Level 1, Unit L1-01 on Apr 01 at 10:00 AM has been confirmed.', 'appointment', 1),
(7,  'Appointment Confirmation', 'Appointment Confirmed',        'Your viewing appointment for Unit A-02 on Apr 01 at 2:00 PM has been confirmed.',  'appointment', 2),
(8,  'Appointment Confirmation', 'Appointment Confirmed',        'Your viewing appointment for Unit A-02 on Apr 05 at 11:00 AM has been confirmed.', 'appointment', 3),
(9,  'Appointment Confirmation', 'Appointment Confirmed',        'Your viewing appointment for Level 1, Unit L1-01 on Apr 07 at 9:30 AM has been confirmed.', 'appointment', 4),
(10, 'Appointment Confirmation', 'Appointment Confirmed',        'Your viewing appointment for Level 1, Unit L1-01 on Apr 08 at 3:00 PM has been confirmed.',  'appointment', 5),
(8,  'Payment Overdue',          'Payment Overdue Notice',       'Your invoice #8 for Unit A-01 is overdue. Outstanding balance: $35,000.00. Please settle immediately.', 'invoice', 8),
(1,  'Payment Overdue',          'Overdue Payment Alert',        'Tenant Carla Mendoza has an overdue invoice #8 ($35,000.00 remaining) for Unit A-01.', 'invoice', 8),
(6,  'Lease Renewal',            'Lease Renewal Reminder',       'Your lease for Unit G-01 expires on Nov 30, 2026. Auto-renewal is enabled with a 5% rate increase.', 'lease', 1),
(8,  'Maintenance Update',       'Maintenance In Progress',      'Your HVAC maintenance request is now being handled by our technician.', 'maintenance_request', 3),
(1,  'General',                  'System Maintenance Scheduled', 'REMS will undergo scheduled maintenance on Mar 20, 2026 from 2:00 AM to 4:00 AM.', NULL, NULL);

-- Application Documents
INSERT INTO application_document (application_id, file_name, file_path, file_type, file_size, uploaded_at)
VALUES
(1, 'anna_business_permit.pdf',    '/uploads/applications/1/anna_business_permit.pdf',    'pdf', 245000,  '2025-11-15 09:30:00'),
(1, 'anna_valid_id.jpg',           '/uploads/applications/1/anna_valid_id.jpg',           'jpg', 180000,  '2025-11-15 09:32:00'),
(1, 'anna_financial_statement.pdf','/uploads/applications/1/anna_financial_statement.pdf','pdf', 520000,  '2025-11-15 09:35:00'),
(2, 'brian_business_permit.pdf',   '/uploads/applications/2/brian_business_permit.pdf',   'pdf', 310000,  '2025-12-01 10:00:00'),
(2, 'brian_valid_id.png',          '/uploads/applications/2/brian_valid_id.png',          'png', 200000,  '2025-12-01 10:05:00'),
(3, 'carla_dti_registration.pdf',  '/uploads/applications/3/carla_dti_registration.pdf',  'pdf', 280000,  '2025-12-05 14:00:00'),
(3, 'carla_valid_id.jpg',          '/uploads/applications/3/carla_valid_id.jpg',          'jpg', 150000,  '2025-12-05 14:10:00'),
(6, 'anna_updated_permit.pdf',     '/uploads/applications/6/anna_updated_permit.pdf',     'pdf', 260000,  '2026-03-18 11:00:00');

-- Lease Documents
INSERT INTO lease_document (lease_id, file_name, file_path, generated_at)
VALUES
(1, 'lease_agreement_anna_unit_g01.pdf',    '/uploads/leases/1/lease_agreement_v1.pdf',   '2025-11-22 10:00:00'),
(2, 'lease_agreement_brian_unit_201.pdf',   '/uploads/leases/2/lease_agreement_v1.pdf',   '2025-12-17 09:00:00'),
(3, 'lease_agreement_carla_unit_a01.pdf',   '/uploads/leases/3/lease_agreement_v1.pdf',   '2025-12-20 11:00:00'),
(4, 'lease_agreement_derek_unit_b01.pdf',   '/uploads/leases/4/lease_agreement_v1.pdf',   '2026-02-03 14:00:00'),
(5, 'lease_agreement_elena_unit_301.pdf',   '/uploads/leases/5/lease_agreement_v1.pdf',   '2026-02-22 10:00:00'),
(1, 'lease_agreement_anna_unit_g01_v2.pdf', '/uploads/leases/1/lease_agreement_v2.pdf',   '2026-02-15 16:00:00');

-- ============================================================
-- DEV USER SAMPLE DATA
-- ============================================================

UPDATE `user` SET
    preferred_payment_cycle = 'Monthly',
    availability_schedule   = 'Mon-Fri 8AM-5PM'
WHERE username = 'dev_admin';

-- Mark units 2 and 4 as Occupied
UPDATE store_unit SET availability = 'Occupied' WHERE unit_id IN (2, 4);

-- Appointments
INSERT INTO appointment (agent_id, tenant_id, unit_id, date_time, end_time, status)
VALUES
(4, 11, 9, '2026-04-02 10:00:00', '2026-04-02 11:00:00', 'Scheduled'),
(11, 9, 7, '2026-04-03 14:00:00', '2026-04-03 15:00:00', 'Scheduled');

-- Rental Applications
INSERT INTO rental_application (tenant_id, unit_id, submission_date, status)
VALUES
(11, 2, '2025-12-15', 'Approved'),   -- Unit G-02 (lease 6 follows)
(11, 4, '2026-02-01', 'Approved'),   -- Unit 2-02 (lease 7 follows)
(11, 7, '2026-03-18', 'Pending');    -- Unit A-02 (Available; exploring expansion)

-- Application Documents
INSERT INTO application_document (application_id, file_name, file_path, file_type, file_size, uploaded_at)
VALUES
(8,  'dev_business_permit.pdf', '/uploads/applications/8/dev_business_permit.pdf', 'pdf', 230000, '2025-12-15 10:00:00'),
(8,  'dev_valid_id.jpg',        '/uploads/applications/8/dev_valid_id.jpg',        'jpg', 170000, '2025-12-15 10:05:00'),
(10, 'dev_updated_permit.pdf',  '/uploads/applications/10/dev_updated_permit.pdf', 'pdf', 250000, '2026-03-18 09:00:00');

-- Leases
INSERT INTO lease (tenant_id, unit_id, start_date, end_date, payment_cycle, status,
                   tenant_signature, tenant_signed_at, agent_signature, agent_signed_at, signature_status,
                   auto_renew, renewal_rate_increase, renewal_status)
VALUES
(11, 2, '2026-01-01', '2026-12-31', 'Monthly', 'Active',
 'esign_dev_001', '2025-12-18 10:00:00', 'esign_mike_002', '2025-12-19 09:00:00', 'Fully Signed',
 1, 5.00, 'Pending Renewal'),
(11, 4, '2026-01-15', '2027-01-14', 'Quarterly', 'Active',
 'esign_dev_002', '2026-01-10 10:00:00', 'esign_mike_003', '2026-01-11 09:00:00', 'Fully Signed',
 0, NULL, 'Not Applicable');

-- Lease Documents
INSERT INTO lease_document (lease_id, file_name, file_path, generated_at)
VALUES
(6, 'lease_agreement_dev_unit_g02.pdf', '/uploads/leases/6/lease_agreement_v1.pdf', '2025-12-20 11:00:00');

-- Invoices
INSERT INTO invoice (lease_id, issue_date, due_date, total_amount, status)
VALUES
(6, '2026-01-01', '2026-02-01', 61000.00, 'Paid'),
(6, '2026-02-01', '2026-03-01', 68650.00, 'Overdue');

-- Payments
INSERT INTO payment (invoice_id, amount, payment_date, due_date, status)
VALUES
(11, 61000.00, '2026-01-20', '2026-02-01', 'Completed'),   -- inv 11 full
(12, 20000.00, '2026-03-10', '2026-03-01', 'Completed');    -- inv 12 partial (20k of 55k, paid after due date)

-- Utility Usage
INSERT INTO utility_usage (unit_id, invoice_id, type, usage_amount, billing_month, amount)
VALUES
(2, 11, 'Electricity',      450.00, '2026-01-01', 4200.00),
(2, 11, 'Water',             30.00, '2026-01-01', 1050.00),
(2, 11, 'Waste Management',   1.50, '2026-01-01',  750.00),
(2, 12, 'Electricity',      480.00, '2026-02-01', 4500.00),
(2, 12, 'Water',             33.00, '2026-02-01', 1150.00);

-- Maintenance Requests
INSERT INTO maintenance_request (lease_id, invoice_id, category, description, priority, status, misuse_flag, charge_amount)
VALUES
(6, NULL, 'Plumbing',        'Water pressure is very low in the restroom area',                  'Medium', 'Open',        0, NULL),
(6, NULL, 'Electrical',      'Power outlet near the storage room is not working',                'High',   'In Progress', 0, NULL),
(6, 12,   'Cosmetic Damage', 'Tenant accidentally damaged the glass display case near entrance', 'Medium', 'Resolved',    1, 8000.00);

-- Notifications
INSERT INTO notification (recipient_id, type, title, message, related_entity, related_id)
VALUES
(11, 'Appointment Confirmation', 'Appointment Confirmed',        'Your viewing appointment for Level 1, Unit L1-01 on Apr 02 at 10:00 AM has been confirmed.', 'appointment', 6),
(11, 'Payment Overdue',          'Payment Overdue Notice',       'Your invoice #12 for Unit G-02 is overdue. Outstanding balance: $48,650.00. Please settle immediately.', 'invoice', 12),
(11, 'Lease Renewal',            'Lease Renewal Reminder',       'Your lease for Unit G-02 expires on Dec 31, 2026. Auto-renewal is enabled with a 5% rate increase.', 'lease', 6),
(11, 'Maintenance Update',       'Maintenance In Progress',      'Your Electrical maintenance request is now being handled by our technician.', 'maintenance_request', 9),
(11, 'General',                  'Welcome to REMS',              'Welcome to the Retail Estate Management System. Manage your leases, pay invoices, and submit maintenance requests from your dashboard.', NULL, NULL);

