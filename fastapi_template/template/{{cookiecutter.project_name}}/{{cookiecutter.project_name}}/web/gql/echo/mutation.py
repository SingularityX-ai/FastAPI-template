import strawberry


@strawberry.type
class Mutation:
    """Echo mutation."""

    @strawberry.field(description="Echo mutation")
    def echo(self, message: str) -> str:
        """
        Sends echo message back to user.

        :param message: incoming message.
        :type message: str
        :return: same message as the incoming.
        :rtype: str
        """
        return message
