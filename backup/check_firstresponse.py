from app import app, OtrsTicket

with app.app_context():
    # 检查FirstResponse字段的情况
    total_tickets = OtrsTicket.query.count()
    print(f"Total tickets: {total_tickets}")
    
    # 检查FirstResponse为空的情况（包括字符串"nan"）
    empty_firstresponse = OtrsTicket.query.filter(
        (OtrsTicket.first_response.is_(None)) | 
        (OtrsTicket.first_response == '') |
        (OtrsTicket.first_response == ' ') |
        (OtrsTicket.first_response == 'nan')
    ).count()
    print(f"Empty FirstResponse tickets: {empty_firstresponse}")
    
    # 检查FirstResponse不为空的情况（排除字符串"nan"）
    non_empty_firstresponse = OtrsTicket.query.filter(
        OtrsTicket.first_response.isnot(None),
        OtrsTicket.first_response != '',
        OtrsTicket.first_response != ' ',
        OtrsTicket.first_response != 'nan'
    ).count()
    print(f"Non-empty FirstResponse tickets: {non_empty_firstresponse}")
    
    # 检查一些样本数据
    print("\nSample FirstResponse values:")
    samples = OtrsTicket.query.with_entities(OtrsTicket.first_response).limit(10).all()
    for i, sample in enumerate(samples):
        print(f"  {i+1}. '{sample[0]}' (type: {type(sample[0])})")
    
    # 检查状态分布，排除Closed和Resolved状态
    open_tickets_with_empty_fr = OtrsTicket.query.filter(
        ((OtrsTicket.first_response.is_(None)) | 
         (OtrsTicket.first_response == '') |
         (OtrsTicket.first_response == ' ') |
         (OtrsTicket.first_response == 'nan')),
        ~OtrsTicket.state.in_(['Closed', 'Resolved'])
    ).count()
    print(f"\nOpen tickets with empty FirstResponse (excluding Closed/Resolved): {open_tickets_with_empty_fr}")
