#!/usr/bin/env python3
"""
Setup PostgreSQL database for game recommendation system
"""
import psycopg2
import getpass

def get_postgres_credentials():
    print("🔐 PostgreSQL Connection Setup")
    print("=" * 40)
    
    # Get credentials from user
    username = input("PostgreSQL username (default: postgres): ").strip() or "postgres"
    password = getpass.getpass("PostgreSQL password: ")
    database = input("Database name (default: postgres): ").strip() or "postgres"
    host = input("Host (default: localhost): ").strip() or "localhost"
    port = input("Port (default: 5432): ").strip() or "5432"
    
    return {
        'host': host,
        'port': int(port),
        'database': database,
        'user': username,
        'password': password
    }

def test_connection(conn_params):
    """Test the connection with provided credentials"""
    try:
        conn = psycopg2.connect(**conn_params)
        print("✅ Connection successful!")
        
        # Test basic functionality
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"📊 PostgreSQL Version: {version}")
        
        # Test if we can create databases
        cursor.execute("SELECT 1;")
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def create_gamequest_database(conn_params):
    """Create the gamequest database"""
    try:
        # Connect to default postgres database first
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'gamequest'")
        if cursor.fetchone():
            print("📁 Database 'gamequest' already exists")
        else:
            # Create the database
            cursor.execute("CREATE DATABASE gamequest")
            print("✅ Created database 'gamequest'")
        
        cursor.close()
        conn.close()
        
        # Now connect to the new database
        gamequest_params = conn_params.copy()
        gamequest_params['database'] = 'gamequest'
        
        return gamequest_params
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return None

if __name__ == "__main__":
    print("🚀 GameQuest Database Setup")
    print("=" * 50)
    
    # Get credentials
    conn_params = get_postgres_credentials()
    
    # Test connection
    if test_connection(conn_params):
        # Create gamequest database
        gamequest_params = create_gamequest_database(conn_params)
        if gamequest_params:
            print("\n🎉 Database setup complete!")
            print(f"📝 Connection details:")
            print(f"   Host: {gamequest_params['host']}")
            print(f"   Port: {gamequest_params['port']}")
            print(f"   Database: {gamequest_params['database']}")
            print(f"   User: {gamequest_params['user']}")
            print("\n🔧 Next steps:")
            print("   1. We'll create the database schema")
            print("   2. Load your game metadata from G:\\Data\\images\\")
            print("   3. Migrate critics data")
    else:
        print("\n❌ Please check your credentials and try again")