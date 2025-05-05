

def user_group_is(user, group_name):
    return user.groups.filter(name=group_name).exists()

def is_seller(user):
    return user_group_is(user, 'Sotuvchi')