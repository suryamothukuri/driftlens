
// DuckDB-Wasm Client-Side Initialization for DriftLens
import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/+esm';

class DriftDBClient {
  constructor() {
    this.db = null;
    this.conn = null;
    this.isReady = false;
    this.readyCallbacks = [];
  }

  async init() {
    try {
      const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();
      const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);
      const worker_url = URL.createObjectURL(
        new Blob([`importScripts("${bundle.mainWorker}");`], { type: 'text/javascript' })
      );

      const worker = new Worker(worker_url);
      const logger = new duckdb.ConsoleLogger();
      this.db = new duckdb.AsyncDuckDB(logger, worker);
      await this.db.instantiate(bundle.mainModule, bundle.pthreadWorker);
      URL.revokeObjectURL(worker_url);

      this.conn = await this.db.connect();
      console.log('DuckDB-Wasm initialized successfully');

      // Attempt to register parquet tables if available
      const tables = ['companies', 'themes', 'theme_intensity', 'theme_changes', 'explanations', 'evidence_chunks', 'data_quality'];
      for (const tbl of tables) {
        try {
          const res = await fetch(`data/${tbl}.parquet`);
          if (res.ok) {
            const buffer = await res.arrayBuffer();
            await this.db.registerFileBuffer(`${tbl}.parquet`, new Uint8Array(buffer));
            await this.conn.query(`CREATE VIEW IF NOT EXISTS ${tbl} AS SELECT * FROM read_parquet('${tbl}.parquet')`);
            console.log(`Registered table: ${tbl}`);
          }
        } catch (e) {
          console.warn(`Could not load data/${tbl}.parquet, using fallback data`);
        }
      }

      this.isReady = true;
      this.readyCallbacks.forEach(cb => cb());
    } catch (err) {
      console.warn('DuckDB initialization fallback:', err);
      this.isReady = true;
      this.readyCallbacks.forEach(cb => cb());
    }
  }

  onReady(callback) {
    if (this.isReady) {
      callback();
    } else {
      this.readyCallbacks.push(callback);
    }
  }

  async query(sql) {
    if (!this.conn) {
      throw new Error("DuckDB connection not active");
    }
    const result = await this.conn.query(sql);
    return result.toArray().map(row => row.toJSON());
  }
}

window.DriftDB = new DriftDBClient();
window.DriftDB.init();
