# Current Daily Statistics Calculation Logic

## Overview
The Daily Statistics feature calculates and stores daily ticket metrics including opening/closing balances, new tickets, resolved tickets, and age distribution.

## Current Implementation Components

### 1. Frontend (`templates/daily_statistics.html`)
- Displays table with columns: Date, Opening Balance, New Tickets, Resolved Tickets, Closing Balance, Age <24h, Age 24-48h, Age 48-72h, Age 72-96h, Age >96h
- Calls `/api/daily-statistics` to fetch data
- Manual trigger via `/api/calculate-daily-stats`

### 2. Backend Routes (`app.py`)
- `/api/daily-statistics` → `analysis_service.get_daily_statistics_data()`
- `/api/calculate-daily-stats` → `scheduler_service.trigger_manual_calculation()`

### 3. Calculation Logic (`services/analysis_service.py::calculate_daily_age_distribution()`)

#### Opening Balance Calculation:
```python
# For subsequent records: use previous day's closing balance
yesterday_stat = DailyStatistics.query.filter_by(statistic_date=yesterday).first()
if yesterday_stat:
    opening_balance = yesterday_stat.closing_balance
else:
    # For first record: total tickets - closed tickets
    total_tickets = OtrsTicket.query.count()
    closed_tickets = OtrsTicket.query.filter(
        OtrsTicket.state.in_(['Closed', 'Resolved', 'Cancelled'])
    ).count()
    opening_balance = total_tickets - closed_tickets
```

#### New Tickets Calculation:
```python
# Tickets created today
new_tickets = OtrsTicket.query.filter(
    db.func.date(OtrsTicket.created_date) == today
).count()
```

#### Resolved Tickets Calculation:
```python
# Tickets closed today
resolved_tickets = OtrsTicket.query.filter(
    db.func.date(OtrsTicket.closed_date) == today
).count()
```

#### Closing Balance Calculation:
```python
# Current open tickets
open_tickets = OtrsTicket.query.filter(OtrsTicket.closed_date.is_(None)).all()
closing_balance = len(open_tickets)
```

#### Age Distribution Calculation:
```python
# Age distribution for current open tickets
for ticket in open_tickets:
    if ticket.age_hours is not None:
        if ticket.age_hours < 24:
            age_lt_24h += 1
        elif ticket.age_hours < 48:
            age_24_48h += 1
        elif ticket.age_hours < 72:
            age_48_72h += 1
        elif ticket.age_hours < 96:
            age_72_96h += 1
        else:
            age_gt_96h += 1
```

### 4. Scheduling (`services/scheduler_service.py`)
- Default schedule: 23:59 daily
- Triggers `calculate_daily_age_distribution()`
- Configurable via UI

### 5. Data Storage
- **DailyStatistics table**: Stores calculated metrics
- **StatisticsLog table**: Stores execution logs

## Key Behavior Notes

1. **Opening Balance Logic**: 
   - First calculation: Total tickets - closed/resolved/cancelled tickets
   - Subsequent days: Previous day's closing balance

2. **Closing Balance**: Always current count of open tickets (closed_date IS NULL)

3. **Age Distribution**: Based on current open tickets at calculation time

4. **Date-based Filtering**: Uses `db.func.date()` for same-day comparisons

5. **State Filtering**: Considers 'Closed', 'Resolved', 'Cancelled' as closed states

## Potential Issues to Review

Please review this logic and let me know what needs to be modified. Common issues might include:

1. **Opening Balance Calculation**: Should it be calculated differently?
2. **State Definitions**: Are the closed states correct?
3. **Age Distribution Timing**: Should it reflect the age at end of day vs current time?
4. **Date Handling**: Any timezone considerations?
5. **Incremental vs Snapshot**: Should it be incremental daily changes or daily snapshots?
