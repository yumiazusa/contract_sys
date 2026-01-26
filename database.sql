-- 创建数据库
CREATE DATABASE IF NOT EXISTS projectdb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE projectdb;

-- 创建合同表
CREATE TABLE IF NOT EXISTS contracts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_no VARCHAR(50) UNIQUE NOT NULL COMMENT '合同编号',
    contract_name VARCHAR(200) NOT NULL COMMENT '合同名称',
    project_no VARCHAR(500) COMMENT '项目号',
    contract_type VARCHAR(20) NOT NULL COMMENT '合同类型',
    platform VARCHAR(10) NOT NULL COMMENT '平台',
    contract_amount DECIMAL(15, 2) COMMENT '合同金额',
    sign_date DATE COMMENT '合同签订日期',
    company_name VARCHAR(200) NOT NULL COMMENT '单位名称',
    contact_phone VARCHAR(50) NOT NULL COMMENT '联系电话',
    manager VARCHAR(100) NOT NULL COMMENT '合同负责人',
    department VARCHAR(50) NOT NULL COMMENT '负责人所在部门',
    payment_terms TEXT COMMENT '合同支付条件',
    original_contract_no VARCHAR(50) COMMENT '原合同编号',
    original_contract_name VARCHAR(200) COMMENT '原合同名称',
    remarks TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_contract_no (contract_no),
    INDEX idx_contract_type (contract_type),
    INDEX idx_platform (platform),
    INDEX idx_department (department),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同信息表';

-- 创建用户表(简单示例)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(建议使用加密)',
    full_name VARCHAR(100) COMMENT '姓名',
    department VARCHAR(50) COMMENT '部门',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    last_login DATETIME COMMENT '最后登录时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

