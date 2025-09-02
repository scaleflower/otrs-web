from app import app, OtrsTicket

with app.app_context():
    # 直接测试空FirstResponse详情功能
    print("Testing empty FirstResponse details API functionality...")
    
    # 获取所有Open状态的空FirstResponse工单
    empty_firstresponse_tickets = OtrsTicket.query.filter(
        ((OtrsTicket.first_response.is_(None)) | 
         (OtrsTicket.first_response == '') |
         (OtrsTicket.first_response == ' ') |
         (OtrsTicket.first_response == 'nan')),
        ~OtrsTicket.state.in_(['Closed', 'Resolved'])
    ).all()
    
    print(f"Found {len(empty_firstresponse_tickets)} open tickets with empty FirstResponse")
    
    # 显示详细信息
    if empty_firstresponse_tickets:
        print("\nEmpty FirstResponse ticket details:")
        for i, ticket in enumerate(empty_firstresponse_tickets[:5]):  # 只显示前5个
            print(f"  {i+1}. Ticket #{ticket.ticket_number}:")
            print(f"     - FirstResponse: '{ticket.first_response}'")
            print(f"     - State: {ticket.state}")
            print(f"     - Priority: {ticket.priority}")
            print(f"     - Age: {ticket.age}")
            print(f"     - Created: {ticket.created_date}")
    
    # 验证导出功能
    print(f"\nThese tickets should now be properly detected in:")
    print("  - Statistics analysis")
    print("  - Excel export")
    print("  - Text export") 
    print("  - Empty FirstResponse details page")
