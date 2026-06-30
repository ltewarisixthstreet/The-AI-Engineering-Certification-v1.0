import aiosqlite

# (name, description, price, category, weight_oz, length_in, width_in, height_in)
PRODUCTS = [
    ("Whisker Wand", "Interactive feather toy on a flexible wand", 9.99, "toys", 2.0, 12.0, 2.0, 2.0),
    ("Catnip Mouse", "Organic catnip-stuffed plush mouse", 4.99, "toys", 1.5, 4.0, 2.0, 2.0),
    ("Laser Pointer Pro", "Red-dot laser with adjustable patterns", 12.99, "toys", 3.0, 5.0, 2.0, 1.0),
    ("Cozy Cat Bed", "Soft donut-shaped bed for curling up", 29.99, "beds", 16.0, 18.0, 18.0, 5.0),
    ("Window Hammock", "Suction-cup window perch with fleece lining", 24.99, "beds", 10.0, 14.0, 10.0, 3.0),
    ("Salmon Treats", "Freeze-dried wild salmon bites, 100g", 7.99, "food", 4.0, 5.0, 3.0, 1.0),
    ("Tuna Crunchies", "Crunchy tuna-flavored dental treats, 80g", 5.99, "food", 3.0, 5.0, 3.0, 1.0),
    ("Scratching Post Tower", "3-tier sisal scratching post with platforms", 49.99, "furniture", 96.0, 16.0, 16.0, 36.0),
]


async def init_db(db: aiosqlite.Connection):
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS oauth_clients (
            client_id TEXT PRIMARY KEY,
            client_info_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS authorization_codes (
            code TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            scopes_json TEXT NOT NULL,
            expires_at REAL NOT NULL,
            code_challenge TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            redirect_uri_provided_explicitly INTEGER NOT NULL,
            resource TEXT,
            username TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS access_tokens (
            token TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            scopes_json TEXT NOT NULL,
            expires_at REAL,
            resource TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            scopes_json TEXT NOT NULL,
            expires_at REAL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            weight_oz REAL NOT NULL DEFAULT 4.0,
            length_in REAL NOT NULL DEFAULT 6.0,
            width_in REAL NOT NULL DEFAULT 4.0,
            height_in REAL NOT NULL DEFAULT 2.0
        );
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            UNIQUE(username, product_id)
        );
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pending_authorizations (
            request_id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            scopes_json TEXT NOT NULL,
            code_challenge TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            redirect_uri_provided_explicitly INTEGER NOT NULL,
            resource TEXT,
            state TEXT,
            expires_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS token_users (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL
        );
        """
    )

    # Migrate: add weight/dimension columns to existing tables
    for col_sql in [
        "ALTER TABLE products ADD COLUMN weight_oz REAL NOT NULL DEFAULT 4.0",
        "ALTER TABLE products ADD COLUMN length_in REAL NOT NULL DEFAULT 6.0",
        "ALTER TABLE products ADD COLUMN width_in REAL NOT NULL DEFAULT 4.0",
        "ALTER TABLE products ADD COLUMN height_in REAL NOT NULL DEFAULT 2.0",
    ]:
        try:
            await db.execute(col_sql)
        except Exception:
            pass

    # Seed products if empty
    cursor = await db.execute("SELECT COUNT(*) FROM products")
    (count,) = await cursor.fetchone()
    if count == 0:
        await db.executemany(
            "INSERT INTO products (name, description, price, category, weight_oz, length_in, width_in, height_in) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            PRODUCTS,
        )
    else:
        # Update weight/dimensions for existing products by name
        for row in PRODUCTS:
            await db.execute(
                """UPDATE products SET weight_oz=?, length_in=?, width_in=?, height_in=?
                   WHERE name=?""",
                (row[4], row[5], row[6], row[7], row[0]),
            )
    await db.commit()
