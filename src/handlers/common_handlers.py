from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.database import add_expense
from services.cache import temp_data_cache

router = Router()

@router.callback_query(F.data.startswith("confirm_expense:"))
async def handle_expense_confirmation(callback: CallbackQuery):
    """
    Handles the callback from the confirmation buttons (Yes/No).
    """
    # Acknowledge the button press to remove the "loading" state on the user's side.
    await callback.answer()

    # Safely unpack the callback data
    try:
        _, action, data_str = callback.data.split(":", 2)
    except ValueError:
        # This will handle cases where the callback data is just "confirm_expense:no"
        _, action = callback.data.split(":", 1)
        data_str = None

    if action == "yes" and data_str:
        # data_str is now the key to our cache
        expense_data = temp_data_cache.get(data_str)

        if not expense_data:
            # This can happen if the bot was restarted after the button was sent
            await callback.message.edit_text(
                "😕 К сожалению, данные для этого подтверждения устарели. "
                "Пожалуйста, отправьте команду еще раз.",
                reply_markup=None
            )
            return

        try:
            amount = float(expense_data['amount'])
            category = expense_data['category']

            # Add expense to the database
            add_expense(amount=amount, category=category)

            # Edit the original message to show success and remove the keyboard
            await callback.message.edit_text(
                f"✅ Я вас понял. Внес расход на сумму **{amount:.2f}** в категорию **'{category}'**."
            )
        except (KeyError, ValueError) as e:
            await callback.message.edit_text(
                f"😕 Произошла ошибка при обработке вашего подтверждения: {e}\n"
                "Пожалуйста, попробуйте еще раз.",
                reply_markup=None # Remove keyboard on error
            )

    elif action == "no":
        # Edit the original message to ask for clarification and remove the keyboard
        await callback.message.edit_text(
            "Пожалуйста, уточните тогда, что вы имели в виду.",
            reply_markup=None # Remove keyboard
        )
    else:
        # Fallback for malformed callback data
        await callback.message.edit_text(
            "😕 Что-то пошло не так с кнопками. Попробуйте отправить команду заново.",
            reply_markup=None # Remove keyboard
        )
