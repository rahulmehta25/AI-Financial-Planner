# How to Get Railway PostgreSQL Public URL

The URL you provided:
```
postgresql://postgres:oKlOSTYHPWxKGQYxlzrptJtNtXxZkoic@postgres.railway.internal:5432/railway
```

This is the **INTERNAL** URL (only works from within Railway).

## To get the PUBLIC URL:

1. Go to your Railway project: https://railway.com/project/b8bab7e2-f74a-40af-b1c2-3f38e25d3bb3

2. Click on your **PostgreSQL** service

3. Go to the **Settings** tab

4. Under **Networking**, click **"Generate Domain"** or **"Enable Public Networking"**

5. Railway will provide a public URL like:
   ```
   postgresql://postgres:oKlOSTYHPWxKGQYxlzrptJtNtXxZkoic@roundhouse.proxy.rlwy.net:12345/railway
   ```

6. Go back to **Variables** tab - you should now see:
   - `DATABASE_URL` - Internal URL (for your app when deployed)
   - `DATABASE_PUBLIC_URL` - Public URL (for external connections)

## Alternative: TCP Proxy

If public networking isn't available, use Railway's TCP proxy:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link to your project
railway login
railway link

# Connect via proxy
railway run python test_railway_db.py
```

This will automatically use the internal URL through Railway's proxy.