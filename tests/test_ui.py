import pytest
from nicegui import ui
from nicegui.testing import User

from quizzy import __main__


pytest_plugins = ["nicegui.testing.user_plugin"]


@pytest.mark.module_under_test(__main__)
async def test_click(user: User) -> None:
    await user.open("/accueil/micronutrition")
    await user.should_see("C'est parti !")
    user.find(ui.button).click()
    await user.should_see("Avec environ combien de follicules commence-t-on la puberté ?")
