import sqlite3
import pandas as pd
from datetime import datetime

def show_database_summary():
    """Display a clean summary of the database contents"""
    try:
        # Connect to the database (it's in the instance folder)
        conn = sqlite3.connect('instance/otrs_data.db')
        
        print("=" * 80)
        print("DATABASE SUMMARY")
        print("=" * 80)
        
        # Show upload sessions summary
        upload_sessions = pd.read_sql_query("""
            SELECT id, session_id, filename, 
                   datetime(upload_time) as upload_time, 
                   total_records 
            FROM upload_session 
            ORDER BY upload_time DESC
        """, conn)
        
        print("\nUPLOAD SESSIONS:")
        print("-" * 80)
        if not upload_sessions.empty:
            for _, session in upload_sessions.iterrows():
                print(f"Session {session['id']}:")
                print(f"  Session ID: {session['session_id']}")
                print(f"  Filename: {session['filename']}")
                print(f"  Upload Time: {session['upload_time']}")
                print(f"  Total Records: {session['total_records']}")
                print()
        else:
            print("No upload sessions found")
        
        # Show ticket statistics
        ticket_stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(DISTINCT session_id) as total_sessions,
                SUM(CASE WHEN closed_date IS NULL THEN 1 ELSE 0 END) as open_tickets,
                SUM(CASE WHEN closed_date IS NOT NULL THEN 1 ELSE 0 END) as closed_tickets,
                COUNT(DISTINCT state) as unique_states,
                COUNT(DISTINCT priority) as unique_priorities
            FROM ticket
        """, conn)
        
        print("TICKET STATISTICS:")
        print("-" * 80)
        if not ticket_stats.empty:
            stats = ticket_stats.iloc[0]
            print(f"Total Tickets: {stats['total_tickets']}")
            print(f"Total Sessions: {stats['total_sessions']}")
            print(f"Open Tickets: {stats['open_tickets']}")
            print(f"Closed Tickets: {stats['closed_tickets']}")
            print(f"Unique States: {stats['unique_states']}")
            print(f"Unique Priorities: {stats['unique_priorities']}")
        else:
            print("No ticket statistics available")
        
        # Show state distribution
        state_distribution = pd.read_sql_query("""
            SELECT state, COUNT(*) as count 
            FROM ticket 
            GROUP BY state 
            ORDER BY count DESC
        """, conn)
        
        print(f"\nSTATE DISTRIBUTION:")
        print("-" * 80)
        if not state_distribution.empty:
            for _, row in state_distribution.iterrows():
                print(f"{row['state'] or 'N/A'}: {row['count']}")
        else:
            print("No state distribution data")
        
        # Show priority distribution
        priority_distribution = pd.read_sql_query("""
            SELECT priority, COUNT(*) as count 
            FROM ticket 
            GROUP BY priority 
            ORDER BY count DESC
        """, conn)
        
        print(f"\nPRIORITY DISTRIBUTION:")
        print("-" * 80)
        if not priority_distribution.empty:
            for _, row in priority_distribution.iterrows():
                print(f"{row['priority'] or 'N/A'}: {row['count']}")
        else:
            print("No priority distribution data")
            
        # Close connection
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    show_database_summary()
