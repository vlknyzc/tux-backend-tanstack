-- Production database table reset script
-- Run this to drop all master_data and users app tables

-- Drop tables in dependency order (children first, parents last)

-- Drop propagation tables
DROP TABLE IF EXISTS master_data_propagationtarget CASCADE;
DROP TABLE IF EXISTS master_data_propagationevent CASCADE;

-- Drop audit tables
DROP TABLE IF EXISTS master_data_stringaudit CASCADE;
DROP TABLE IF EXISTS master_data_ruleaudit CASCADE;
DROP TABLE IF EXISTS master_data_dimensionaudit CASCADE;

-- Drop string-related tables
DROP TABLE IF EXISTS master_data_stringupdatebatch CASCADE;
DROP TABLE IF EXISTS master_data_stringmodification CASCADE;
DROP TABLE IF EXISTS master_data_stringinheritanceupdate CASCADE;
DROP TABLE IF EXISTS master_data_stringdetail CASCADE;
DROP TABLE IF EXISTS master_data_string CASCADE;

-- Drop rule-related tables
DROP TABLE IF EXISTS master_data_ruledetail CASCADE;
DROP TABLE IF EXISTS master_data_rule CASCADE;

-- Drop submission table
DROP TABLE IF EXISTS master_data_submission CASCADE;

-- Drop dimension-related tables
DROP TABLE IF EXISTS master_data_dimensionvalue CASCADE;
DROP TABLE IF EXISTS master_data_dimension CASCADE;

-- Drop field and platform tables
DROP TABLE IF EXISTS master_data_field CASCADE;
DROP TABLE IF EXISTS master_data_platform CASCADE;

-- Drop users app tables
DROP TABLE IF EXISTS users_workspaceuser CASCADE;

-- Drop workspace table (last, as others depend on it)
DROP TABLE IF EXISTS master_data_workspace CASCADE;

-- Drop propagation settings
DROP TABLE IF EXISTS master_data_propagationsettings CASCADE;
DROP TABLE IF EXISTS master_data_propagationjob CASCADE;
DROP TABLE IF EXISTS master_data_propagationerror CASCADE;

-- Clear migration history for these apps
DELETE FROM django_migrations WHERE app = 'master_data';
DELETE FROM django_migrations WHERE app = 'users' AND name = '0002_add_workspace_relationships';
