import sqlite3

limit_rows = 50


def open_db(base_path):
    # Connect to your database
    conn = sqlite3.connect(f"{base_path}/04_sqlite/data.db")
    conn.execute("PRAGMA cache_size = -10485760;")
    return conn


def get_top_variants_in_cluster(conn: sqlite3.Connection, sample_names):
    cur = conn.cursor()

    # SQL query
    query = f"""
    WITH cluster_sample_ids AS (
        SELECT id
        FROM samples
        WHERE name IN ({", ".join(["?"] * len(sample_names))})
    )
    SELECT
        variants.id,
        variants.chr,
        variants.pos,
        variants.ref,
        variants.alt,
        AVG(CASE WHEN sample_id IN cluster_sample_ids THEN gt END) AS in_cluster_gt_avg,
        AVG(CASE WHEN sample_id NOT IN cluster_sample_ids THEN gt END) AS out_cluster_gt_avg,
        AVG(CASE WHEN sample_id IN cluster_sample_ids THEN gt END) - AVG(CASE WHEN sample_id NOT IN cluster_sample_ids THEN gt END) as diff_gt_avg
    FROM genotypes
    INNER JOIN variants ON variants.id = genotypes.variant_id
    GROUP BY variants.id
    HAVING diff_gt_avg > 0
    ORDER BY diff_gt_avg DESC
    LIMIT {limit_rows}
    """

    cur.execute(query, sample_names)
    # Get column names
    columns = [desc[0] for desc in cur.description]

    # Fetch rows
    rows = cur.fetchall()

    # Convert to list of dicts
    results = [dict(zip(columns, row)) for row in rows]

    # Cleanup
    cur.close()
    return results
