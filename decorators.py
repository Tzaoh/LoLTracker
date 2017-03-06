from settings import OWNER_ID


def owner(func):
    # Algo similar aquí:
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator
    def owner_and_call(*args, **kwargs):
        update = args[2]
        if OWNER_ID == update.message.from_user.id:
            return func(*args, **kwargs)
        # raise Exception('Authentication Failed.')
    return owner_and_call


def private(func):
    def private_and_call(*args, **kwargs):
        update = args[2]
        if update.message.chat_id > 0:
            return func(*args, **kwargs)
        # raise Exception('Not private chat.')
    return private_and_call
