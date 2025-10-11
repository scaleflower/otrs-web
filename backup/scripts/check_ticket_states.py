#!/usr/bin/env python3
"""
Script to check ticket state and closed_date consistency
"""

import sqlite3

def check_ticket_states():
    conn = sqlite3.connect('db/otrs_data.db')
    cursor = conn.cursor()

    # Count by state
    cursor.execute('SELECT state, COUNT(*) FROM otrs_ticket GROUP BY state')
    state_counts = cursor.fetchall()
    print('Ticket counts by state:')
    for state, count in state_counts:
        print(f'  {state}: {count}')

    # Count closed_date NULL vs NOT NULL
    cursor.execute('SELECT COUNT(*) FROM otrs_ticket WHERE closed_date IS NULL')
    closed_date_null = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM otrs_ticket WHERE closed_date IS NOT NULL')
    closed_date_not_null = cursor.fetchone()[0]
    print(f'Closed_date NULL: {closed_date_null}')
    print(f'Closed_date NOT NULL: {closed_date_not_null}')

    # Check for tickets that might be in inconsistent states
    cursor.execute("SELECT COUNT(*) FROM otrs_ticket WHERE closed_date IS NULL AND state IN ('Closed', 'Resolved', 'Cancelled')")
    inconsistent_count = cursor.fetchone()[0]
    print(f'Tickets with closed_date=NULL but state in [Closed, Resolved, Cancelled]: {inconsistent_count}')

    cursor.execute("SELECT COUNT(*) FROM otrs_ticket WHERE closed_date IS NOT NULL AND state NOT IN ('Closed', 'Resolved', 'Cancelled')")
    inconsistent_count2 = cursor.fetchone()[0]
    print(f'Tickets with closed_date NOT NULL but state not in [Closed, Resolved, Cancelled]: {inconsistent_count2}')

    conn.close()

if __name__ == '__main__':
    check_ticket_states()
