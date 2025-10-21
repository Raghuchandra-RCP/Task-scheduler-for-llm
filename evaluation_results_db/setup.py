#!/usr/bin/env python3
"""
Setup script for Evaluation Results Database
Creates tables and runs initial tests
"""

import os
import sys
import subprocess
from pathlib import Path

def run_sql_script(sql_file_path):
    """Run a SQL script using psql"""
    try:
        # Get database URL from config
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config import DATABASE_URL
        
        # Extract database connection details from URL
        # Format: postgresql://user:password@host:port/database
        if DATABASE_URL.startswith('postgresql://'):
            # Parse the URL
            url_parts = DATABASE_URL.replace('postgresql://', '').split('/')
            db_name = url_parts[1]
            auth_host = url_parts[0].split('@')
            
            if len(auth_host) == 2:
                auth, host_port = auth_host
                user, password = auth.split(':')
                host, port = host_port.split(':')
            else:
                print("❌ Invalid database URL format")
                return False
            
            # Build psql command
            cmd = [
                'psql',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', db_name,
                '-f', str(sql_file_path)
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            print(f"🔧 Running SQL script: {sql_file_path}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ SQL script executed successfully")
                if result.stdout:
                    print("Output:", result.stdout)
                return True
            else:
                print(f"❌ SQL script failed: {result.stderr}")
                return False
                
        else:
            print("❌ Unsupported database URL format")
            return False
            
    except Exception as e:
        print(f"❌ Error running SQL script: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Evaluation Results Database Setup")
    print("=" * 50)
    
    # Get the current directory
    current_dir = Path(__file__).parent
    sql_file = current_dir / "sql" / "01_create_evaluation_tables.sql"
    
    # Check if SQL file exists
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    print(f"📁 Current directory: {current_dir}")
    print(f"📄 SQL file: {sql_file}")
    
    # Run the SQL script
    print("\n🔧 Creating database tables...")
    success = run_sql_script(sql_file)
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("\n🧪 Running tests...")
        
        # Run the test script
        test_file = current_dir / "tests" / "test_evaluation_db.py"
        if test_file.exists():
            try:
                result = subprocess.run([sys.executable, str(test_file)], 
                                      capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Errors:", result.stderr)
            except Exception as e:
                print(f"❌ Error running tests: {e}")
        else:
            print("⚠️ Test file not found, skipping tests")
        
        print("\n🎉 Setup complete!")
        print("\n📋 Next steps:")
        print("1. Update your evaluators to use the database utilities")
        print("2. Run evaluations to start collecting data")
        print("3. Use analytics queries to analyze results")
        
    else:
        print("\n❌ Database setup failed!")
        print("Please check:")
        print("1. PostgreSQL is running")
        print("2. Database credentials are correct")
        print("3. You have permission to create tables")

if __name__ == "__main__":
    main()
