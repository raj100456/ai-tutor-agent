# Import concrete classes so @IntegrationRegistry.register() decorators execute.
from src.integrations.notifier import discord, email  # noqa: F401
