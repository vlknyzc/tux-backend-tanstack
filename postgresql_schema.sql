CREATE TABLE "django_migrations" (
    "id" SERIAL PRIMARY KEY,
    "app" VARCHAR(255) NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "applied" TIMESTAMP NOT NULL
);

CREATE TABLE "auth_group_permissions" (
    "id" SERIAL PRIMARY KEY,
    "group_id" INTEGER NOT NULL,
    "permission_id" INTEGER NOT NULL,
    FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("group_id", "permission_id")
);

CREATE TABLE "auth_user_groups" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    "group_id" INTEGER NOT NULL,
    FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("user_id", "group_id")
);

CREATE TABLE "auth_user_user_permissions" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    "permission_id" INTEGER NOT NULL,
    FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("permission_id") REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("user_id", "permission_id")
);

CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");

CREATE TABLE "django_admin_log" (
    "id" SERIAL PRIMARY KEY,
    "object_id" TEXT NULL,
    "object_repr" VARCHAR(200) NOT NULL,
    "action_flag" SMALLINT NOT NULL CHECK ("action_flag" >= 0),
    "change_message" TEXT NOT NULL,
    "content_type_id" INTEGER NULL,
    "user_id" INTEGER NOT NULL,
    "action_time" TIMESTAMP NOT NULL,
    FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");

CREATE TABLE "django_content_type" (
    "id" SERIAL PRIMARY KEY,
    "app_label" VARCHAR(100) NOT NULL,
    "model" VARCHAR(100) NOT NULL,
    UNIQUE ("app_label", "model")
);

CREATE TABLE "auth_permission" (
    "id" SERIAL PRIMARY KEY,
    "content_type_id" INTEGER NOT NULL,
    "codename" VARCHAR(100) NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("content_type_id", "codename")
);

CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");

CREATE TABLE "auth_group" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE "auth_user" (
    "id" SERIAL PRIMARY KEY,
    "password" VARCHAR(128) NOT NULL,
    "last_login" TIMESTAMP NULL,
    "is_superuser" BOOLEAN NOT NULL,
    "username" VARCHAR(150) NOT NULL UNIQUE,
    "last_name" VARCHAR(150) NOT NULL,
    "email" VARCHAR(254) NOT NULL,
    "is_staff" BOOLEAN NOT NULL,
    "is_active" BOOLEAN NOT NULL,
    "date_joined" TIMESTAMP NOT NULL,
    "first_name" VARCHAR(150) NOT NULL
);

CREATE TABLE "master_data_field" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "name" VARCHAR(30) NOT NULL,
    "field_level" SMALLINT NOT NULL,
    "next_field_id" BIGINT NULL,
    "platform_id" BIGINT NOT NULL,
    FOREIGN KEY ("next_field_id") REFERENCES "master_data_field" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("platform_id") REFERENCES "master_data_platform" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("platform_id", "name", "field_level")
);

CREATE INDEX "master_data_field_next_field_id_028c5d89" ON "master_data_field" ("next_field_id");
CREATE INDEX "master_data_field_platform_id_1dfa112d" ON "master_data_field" ("platform_id");

CREATE TABLE "master_data_platform" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "platform_type" VARCHAR(30) NOT NULL,
    "name" VARCHAR(30) NOT NULL
);

CREATE TABLE "master_data_dimensionvalue" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "valid_from" DATE NULL,
    "definition" TEXT NULL,
    "dimension_value" VARCHAR(30) NOT NULL,
    "valid_until" DATE NULL,
    "dimension_value_label" VARCHAR(50) NOT NULL,
    "dimension_value_utm" VARCHAR(30) NOT NULL,
    "dimension_id" BIGINT NOT NULL,
    "parent_id" BIGINT NULL,
    FOREIGN KEY ("dimension_id") REFERENCES "master_data_dimension" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("parent_id") REFERENCES "master_data_dimensionvalue" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("dimension_id", "dimension_value")
);

CREATE INDEX "master_data_dimensionvalue_dimension_id_56f46ab9" ON "master_data_dimensionvalue" ("dimension_id");
CREATE INDEX "master_data_dimensionvalue_parent_id_6a07b214" ON "master_data_dimensionvalue" ("parent_id");

CREATE TABLE "master_data_workspace" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "name" VARCHAR(30) NOT NULL UNIQUE,
    "created_by_id" INTEGER NOT NULL,
    "logo" VARCHAR(100) NULL,
    "status" VARCHAR(30) NOT NULL,
    FOREIGN KEY ("created_by_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX "master_data_workspace_created_by_id_48e51333" ON "master_data_workspace" ("created_by_id");

CREATE TABLE "master_data_dimension" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "definition" TEXT NULL,
    "dimension_type" VARCHAR(30) NOT NULL,
    "name" VARCHAR(30) NOT NULL UNIQUE,
    "status" VARCHAR(30) NOT NULL,
    "parent_id" BIGINT NULL,
    FOREIGN KEY ("parent_id") REFERENCES "master_data_dimension" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX "master_data_dimension_parent_id_366b2d7e" ON "master_data_dimension" ("parent_id");

CREATE TABLE "master_data_ruledetail" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "prefix" VARCHAR(20) NULL,
    "suffix" VARCHAR(20) NULL,
    "delimiter" VARCHAR(1) NULL,
    "dimension_order" SMALLINT NOT NULL,
    "dimension_id" BIGINT NOT NULL,
    "rule_id" BIGINT NOT NULL,
    "field_id" BIGINT NOT NULL,
    FOREIGN KEY ("dimension_id") REFERENCES "master_data_dimension" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("rule_id") REFERENCES "master_data_rule" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("field_id") REFERENCES "master_data_field" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("rule_id", "field_id", "dimension_id", "dimension_order")
);

CREATE INDEX "master_data_ruledetail_dimension_id_2ea66512" ON "master_data_ruledetail" ("dimension_id");
CREATE INDEX "master_data_ruledetail_rule_id_a5c2ff1d" ON "master_data_ruledetail" ("rule_id");
CREATE INDEX "master_data_ruledetail_field_id_efa0cce0" ON "master_data_ruledetail" ("field_id");

CREATE TABLE "master_data_rule" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "name" VARCHAR(50) NOT NULL,
    "status" VARCHAR(30) NOT NULL,
    "platform_id" BIGINT NOT NULL,
    "description" TEXT NULL,
    FOREIGN KEY ("platform_id") REFERENCES "master_data_platform" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX "master_data_rule_platform_id_c2860211" ON "master_data_rule" ("platform_id");

CREATE TABLE "master_data_submission" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "name" VARCHAR(30) NOT NULL,
    "description" TEXT NULL,
    "status" VARCHAR(30) NOT NULL,
    "rule_id" BIGINT NOT NULL,
    FOREIGN KEY ("rule_id") REFERENCES "master_data_rule" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX "master_data_submission_rule_id_1e526e04" ON "master_data_submission" ("rule_id");

CREATE TABLE "master_data_string" (
    "id" SERIAL PRIMARY KEY,
    "last_updated" TIMESTAMP NOT NULL,
    "created" TIMESTAMP NOT NULL,
    "field_id" BIGINT NOT NULL,
    "string_uuid" CHAR(32) NOT NULL,
    "parent_uuid" CHAR(32) NULL,
    "value" VARCHAR(400) NOT NULL,
    "submission_id" BIGINT NOT NULL,
    "parent_id" BIGINT NULL,
    FOREIGN KEY ("field_id") REFERENCES "master_data_field" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("submission_id") REFERENCES "master_data_submission" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("parent_id") REFERENCES "master_data_string" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX "master_data_string_field_id_b56d8e4a" ON "master_data_string" ("field_id");
CREATE INDEX "master_data_string_submission_id_221ba67a" ON "master_data_string" ("submission_id");
CREATE INDEX "master_data_string_parent_id_1ee0d17a" ON "master_data_string" ("parent_id");

CREATE TABLE "django_session" (
    "session_key" VARCHAR(40) NOT NULL PRIMARY KEY,
    "session_data" TEXT NOT NULL,
    "expire_date" TIMESTAMP NOT NULL
);

CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");

CREATE TABLE "master_data_stringdetail" (
    "id" SERIAL PRIMARY KEY,
    "created" TIMESTAMP NOT NULL,
    "last_updated" TIMESTAMP NOT NULL,
    "dimension_value_freetext" VARCHAR(100) NULL,
    "string_id" BIGINT NOT NULL,
    "dimension_id" BIGINT NOT NULL,
    "dimension_value_id" BIGINT NULL,
    FOREIGN KEY ("string_id") REFERENCES "master_data_string" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("dimension_id") REFERENCES "master_data_dimension" ("id") DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY ("dimension_value_id") REFERENCES "master_data_dimensionvalue" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX "master_data_stringdetail_string_id_a7e3fdd3" ON "master_data_stringdetail" ("string_id");
CREATE INDEX "master_data_stringdetail_dimension_id_8bd2b7c6" ON "master_data_stringdetail" ("dimension_id");
CREATE INDEX "master_data_stringdetail_dimension_value_id_92062523" ON "master_data_stringdetail" ("dimension_value_id"); 