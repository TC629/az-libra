CREATE TABLE "measurements" (

    "id" integer PRIMARY KEY AUTOINCREMENT,
    "product_id" integer NOT NULL,
    "scale_id" integer NOT NULL,
    "weight" real NOT NULL, -- en gramos
    "timestamp" text NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY("product_id") REFERENCES "products"("id")
);

CREATE TABLE "products" (
    "id" integer PRIMARY KEY AUTOINCREMENT,
    "name" text NOT NULL UNIQUE,
    "min_weight" real NOT NULL, -- en gramos
    "max_weight" real NOT NULL  -- en gramos
);
