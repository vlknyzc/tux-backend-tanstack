# Generated manually to fix production dimension unique constraints

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0009_remove_selected_parent_string"),
    ]

    operations = [
        # Remove the old global unique constraint on name field if it exists
        migrations.RunSQL(
            sql="""
                -- For PostgreSQL
                DO $$
                BEGIN
                    -- Check if the old unique constraint exists and drop it
                    IF EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'master_data_dimension_name_key' 
                        AND table_name = 'master_data_dimension'
                    ) THEN
                        ALTER TABLE master_data_dimension DROP CONSTRAINT master_data_dimension_name_key;
                    END IF;
                    
                    -- Check if old unique index exists and drop it
                    IF EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'master_data_dimension_name_key'
                    ) THEN
                        DROP INDEX master_data_dimension_name_key;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                -- Reverse operation (add back global unique constraint - not recommended)
                ALTER TABLE master_data_dimension ADD CONSTRAINT master_data_dimension_name_key UNIQUE (name);
            """,
        ),
        
        # Ensure workspace-scoped unique constraints are properly set
        migrations.RunSQL(
            sql="""
                -- Create workspace-scoped unique constraints if they don't exist
                DO $$
                BEGIN
                    -- Create unique index for workspace + name if it doesn't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'master_data_dimension_workspace_id_name_3651ff50_uniq'
                    ) THEN
                        CREATE UNIQUE INDEX master_data_dimension_workspace_id_name_3651ff50_uniq 
                        ON master_data_dimension (workspace_id, name);
                    END IF;
                    
                    -- Create unique index for workspace + slug if it doesn't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'master_data_dimension_workspace_id_slug_49d3e9a4_uniq'
                    ) THEN
                        CREATE UNIQUE INDEX master_data_dimension_workspace_id_slug_49d3e9a4_uniq 
                        ON master_data_dimension (workspace_id, slug);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                -- Remove workspace-scoped unique constraints
                DROP INDEX IF EXISTS master_data_dimension_workspace_id_name_3651ff50_uniq;
                DROP INDEX IF EXISTS master_data_dimension_workspace_id_slug_49d3e9a4_uniq;
            """,
        ),
    ]
