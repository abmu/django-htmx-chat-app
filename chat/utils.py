def get_group_name(username_1, username_2):
    if username_1 < username_2:
        return f'chat_{username_1}_{username_2}'
    return f'chat_{username_2}_{username_1}'