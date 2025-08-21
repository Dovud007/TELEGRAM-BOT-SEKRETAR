from aiogram.fsm.state import State, StatesGroup

class ExpenseConversation(StatesGroup):
    """
    Defines the states for the multi-step expense logging conversation.
    """
    # State when the bot has asked for amounts for multiple dates and is waiting for the user's reply.
    waiting_for_amounts = State()

    # State when the bot has asked the user to clarify the entire expense command.
    waiting_for_clarification = State()
