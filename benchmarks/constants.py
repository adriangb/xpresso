# Establishing an asyncpg -> PostgreSQL connection takes ~75ms
# Running query takes about 1ms
# Hitting okta.com w/ httpx takes ~100ms
# So we'll take a range of 1ms to 100ms as delays for async dependencies
# And then make a medium sized DAG (3 levels)

NO_DELAY = (0, 0)
DELAY = (1e-3, 1e-1)

DAG_SHAPE = (3, 2, 2)
