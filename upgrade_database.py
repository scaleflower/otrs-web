#!/usr/bin/env python3
"""
Database upgrade script to add Responsible column to otrs_ticket table
"""

from app import app, db
from sqlalchemy import text

def upgrade_database():
    """Upgrade database to add Responsible column"""
    print("Starting database upgrade...")
    
    with app.app_context():
        # Check if responsible column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('otrs_ticket')]
        
        if 'responsible' in columns:
            print("✓ Responsible column already exists in otrs_ticket table")
            return True
        
        # Backup database first
        print("Creating database backup...")
        import shutil
        import os
        from datetime import datetime
        
        backup_dir = 'database_backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"otrs_backup_pre_upgrade_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        if os.path.exists('instance/otrs_data.db'):
            shutil.copy2('instance/otrs_data.db', backup_path)
            print(f"✓ Database backup created: {backup_path}")
        else:
            print("⚠ No existing database found, proceeding without backup")
        
        # Add responsible column to otrs_ticket table
        print("Adding responsible column to otrs_ticket table...")
        try:
            # SQLite specific ALTER TABLE syntax
            with db.engine.connect() as connection:
                connection.execute(text('ALTER TABLE otrs_ticket ADD COLUMN responsible VARCHAR(255)'))
                connection.commit()
            
            print("✓ Successfully added responsible column to otrs_ticket table")
            
            # Verify the column was added
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('otrs_ticket')]
            if 'responsible' in columns:
                print("✓ Verification passed: responsible column exists")
                return True
            else:
                print("✗ Verification failed: responsible column not found")
                return False
                
        except Exception as e:
            print(f"✗ Error adding responsible column: {str(e)}")
            return False

def create_test_data():
    """Create test data with responsible field"""
    print("\nCreating test data with responsible field...")
    
    with app.app_context():
        from app import OtrsTicket
        from datetime import datetime, timedelta
        import json
        
        # Clear existing test data
        OtrsTicket.query.filter(OtrsTicket.data_source == 'test_upgrade').delete()
        db.session.commit()
        
        # Create test tickets with responsible field
        responsibles = ['张三', '李四', '王五', '赵六']
        
        for i in range(10):
            ticket = OtrsTicket(
                ticket_number=f"UPGRADE-{i:04d}",
                created_date=datetime.now() - timedelta(days=i),
                state='open',
                priority='3 normal',
                first_response='Test response',
                age=f"{i % 3}d {i % 24}h",
                age_hours=(i % 3) * 24 + (i % 24),
                queue='Test Queue',
                owner=f"owner_{i}",
                customer_id=f"CUST-{i:03d}",
                customer_realname=f"Customer {i}",
                title=f"Upgrade Test Ticket {i}",
                service='Test Service',
                type='Incident',
                category='Test Category',
                sub_category='Test Sub Category',
                responsible=responsibles[i % len(responsibles)],
                data_source='test_upgrade',
                raw_data=json.dumps({"test": "upgrade_data"})
            )
            db.session.add(ticket)
        
        db.session.commit()
        print("✓ Test data created successfully with responsible field")

def test_responsible_functionality():
    """Test responsible-related functionality"""
    print("\nTesting responsible functionality...")
    
    with app.app_context():
        from app import OtrsTicket
        
        # Test querying by responsible
        responsibles = OtrsTicket.query.with_entities(OtrsTicket.responsible).distinct().all()
        responsible_list = [r[0] for r in responsibles if r[0] is not None]
        print(f"Unique responsibles found: {responsible_list}")
        
        # Test counting by responsible
        for responsible in responsible_list:
            count = OtrsTicket.query.filter_by(responsible=responsible).count()
            print(f"  {responsible}: {count} tickets")
        
        print("✓ Responsible functionality test completed")

def main():
    """Main function"""
    print("=" * 60)
    print("OTRS Database Upgrade Script")
    print("=" * 60)
    print("This script will:")
    print("1. Add 'responsible' column to otrs_ticket table")
    print("2. Create test data to verify the upgrade")
    print("3. Test responsible-related functionality")
    print("=" * 60)
    
    # Run upgrade
    success = upgrade_database()
    
    if success:
        # Create test data
        create_test_data()
        
        # Test functionality
        test_responsible_functionality()
        
        print("\n" + "=" * 60)
        print("🎉 Database upgrade completed successfully!")
        print("The responsible column has been added and is ready for use.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Database upgrade failed!")
        print("Please check the error messages above.")
        print("=" * 60)
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
