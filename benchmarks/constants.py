# Establishing an asyncpg -> PostgreSQL connection takes ~75ms
# Running query takes about 1ms
# Hitting okta.com w/ httpx takes ~100ms
# So we'll take a range of 1ms to 100ms as delays for async dependencies
# And then make a medium sized DAG (3 levels)

NO_DELAY = (0, 0)
DELAY = (1e-3, 1e-1)

DAG_SHAPE = (3, 2, 2)

ROUTING_PATHS = {
    "one": {
        "one-one": {
            "one-one-one": None,
            "one-one-two": None,
            "one-one-three": None,
        },
        "one-two": {
            "one-two-one": None,
            "one-two-two": None,
            "one-two-three": None,
        },
        "one-three": {
            "one-three-one": None,
            "one-three-two": None,
            "one-three-three": None,
        },
    },
    "two": {
        "two-one": {
            "two-one-one": None,
            "two-one-two": None,
            "two-one-three": None,
        },
        "two-two": {
            "two-two-one": None,
            "two-two-two": None,
            "two-two-three": None,
        },
        "two-three": {
            "two-three-one": None,
            "two-three-two": None,
            "two-three-three": None,
        },
    },
}
