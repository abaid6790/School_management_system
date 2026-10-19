def compute_net_salary(record):
    """basic + allowances + bonus - deductions. Never stored: pure arithmetic on
    the row's own columns, so storing it would only add a place to go stale."""
    return record.basic_salary + record.allowances + record.bonus - record.deductions
