from app import app, OtrsTicket

with app.app_context():
    # 测试空FirstResponse检测逻辑
    print("Testing empty FirstResponse detection logic...")
    
    # 获取所有Open状态的工单
    open_tickets = OtrsTicket.query.filter(
        ~OtrsTicket.state.in_(['Closed', 'Resolved'])
    ).all()
    
    print(f"Total open tickets: {len(open_tickets)}")
    
    # 手动检查FirstResponse字段
    empty_firstresponse_count = 0
    empty_firstresponse_tickets = []
    
    for ticket in open_tickets:
        first_response = ticket.first_response
        # 检查是否为空的FirstResponse（包括None、空字符串、空格、字符串"nan"）
        if (first_response is None or 
            first_response == '' or 
            first_response == ' ' or 
            str(first_response).lower() == 'nan'):
            empty_firstresponse_count += 1
            empty_firstresponse_tickets.append({
                'ticket_number': ticket.ticket_number,
                'first_response': ticket.first_response,
                'state': ticket.state
            })
    
    print(f"Manual check - Open tickets with empty FirstResponse: {empty_firstresponse_count}")
    
    # 显示前几个空FirstResponse的工单
    print("\nSample empty FirstResponse tickets:")
    for i, ticket in enumerate(empty_firstresponse_tickets[:5]):
        print(f"  {i+1}. Ticket #{ticket['ticket_number']}: FirstResponse='{ticket['first_response']}', State={ticket['state']}")
    
    # 使用数据库查询检查
    db_empty_count = OtrsTicket.query.filter(
        ((OtrsTicket.first_response.is_(None)) | 
         (OtrsTicket.first_response == '') |
         (OtrsTicket.first_response == ' ') |
         (OtrsTicket.first_response == 'nan')),
        ~OtrsTicket.state.in_(['Closed', 'Resolved'])
    ).count()
    
    print(f"Database query - Open tickets with empty FirstResponse: {db_empty_count}")
    
    # 验证结果是否一致
    if empty_firstresponse_count == db_empty_count:
        print("✓ Manual check and database query results match!")
    else:
        print(f"✗ Results don't match! Manual: {empty_firstresponse_count}, DB: {db_empty_count}")
