# DBeaver Refresh Guide - See Updated Tables

## Issue: Can't See Tables in DBeaver

The tables exist in the database `tuition_master_db`. Follow these steps to see them in DBeaver.

---

## Step 1: Verify Database Connection

### Check Your Current Connection in DBeaver:

1. **Look at your connection name** in DBeaver's Database Navigator
2. **Right-click on the connection** → **Edit Connection**
3. **Check the Database field** - it should be: `tuition_master_db`

### Correct Connection Settings:

```
Host: localhost
Port: 5432
Database: tuition_master_db  ← IMPORTANT: Must be this exact name
Username: navaneethn
Password: (leave empty)
```

---

## Step 2: Refresh DBeaver Connection

### Method 1: Refresh Connection (Recommended)

1. **Right-click on your PostgreSQL connection** in Database Navigator
2. Click **"Refresh"** or press `F5`
3. Wait for DBeaver to reload the database structure

### Method 2: Disconnect and Reconnect

1. **Right-click on connection** → **Disconnect**
2. **Right-click again** → **Connect**
3. Expand the connection to see databases

### Method 3: Refresh Specific Database

1. **Expand your connection**
2. **Expand "Databases"**
3. **Right-click on "tuition_master_db"** → **Refresh**
4. **Expand "Schemas"** → **public**
5. **Expand "Tables"** - you should see all 7 tables

---

## Step 3: Verify You're Looking at the Right Database

### In DBeaver SQL Editor:

1. Open SQL Editor: `Database > SQL Editor > New SQL Script`
2. Run this query:

```sql
SELECT current_database();
```

**Expected result:** `tuition_master_db`

If it shows a different database (like `postgres`), you need to:
- Switch to the correct database in DBeaver
- Or create a new connection specifically for `tuition_master_db`

---

## Step 4: List All Tables

Run this query in DBeaver SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected result:** You should see 7 tables:
- classes
- schools
- students
- study_materials
- subjects
- teachers
- users

---

## Step 5: If Tables Still Don't Appear

### Option A: Create New Connection

1. **Database > New Database Connection**
2. Select **PostgreSQL**
3. Fill in:
   ```
   Host: localhost
   Port: 5432
   Database: tuition_master_db
   Username: navaneethn
   Password: (empty)
   ```
4. Click **Test Connection** → **Finish**
5. Expand the new connection to see tables

### Option B: Verify Tables Exist (Command Line)

Run this in terminal to confirm tables exist:

```bash
psql -d tuition_master_db -c "\dt"
```

You should see all 7 tables listed.

---

## Step 6: View Table Structure

Once you can see the tables:

1. **Expand "Tables"** in DBeaver
2. **Right-click on "users"** → **View Data** (to see data)
3. **Right-click on "users"** → **Properties** (to see structure)
4. **Right-click on "users"** → **Generate SQL > DDL** (to see CREATE statement)

---

## Quick Verification Query

Run this in DBeaver SQL Editor to verify everything:

```sql
-- Check database
SELECT current_database() as current_db;

-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check users table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- Check foreign key relationships
SELECT 
    tc.table_name as child_table,
    kcu.column_name as child_column,
    ccu.table_name as parent_table
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;
```

---

## Common Issues

### Issue: "Database tuition_master_db does not exist"

**Solution:** The database exists. Make sure you're connecting to the right PostgreSQL server (localhost:5432) and using the correct database name.

### Issue: "Permission denied"

**Solution:** Make sure you're using username `navaneethn` (or the user that created the database).

### Issue: Tables show in SQL query but not in Navigator

**Solution:** 
1. Right-click on connection → **Refresh** (F5)
2. Or restart DBeaver
3. Check if you're looking at the correct schema (should be "public")

---

## Connection String Reference

For your FastAPI app (already configured):
```
postgresql://navaneethn@localhost:5432/tuition_master_db
```

For DBeaver:
- Host: `localhost`
- Port: `5432`
- Database: `tuition_master_db`
- Username: `navaneethn`
- Password: (empty)

---

## Still Having Issues?

1. **Check PostgreSQL is running:**
   ```bash
   pg_isready
   ```

2. **Verify database exists:**
   ```bash
   psql -l | grep tuition_master_db
   ```

3. **List tables directly:**
   ```bash
   psql -d tuition_master_db -c "\dt"
   ```

If tables show in command line but not in DBeaver, it's a DBeaver refresh/cache issue. Try disconnecting and reconnecting.


