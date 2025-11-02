# Trial Embedding Analysis - Current Behavior

## Current Flow

### When `run_trial_embedding_generation()` is called:

1. **Gets current trials from database** (line 162)
   - Calls `get_detailed_trial_data()` which queries database
   - Returns ALL current trials (e.g., 47 trials)

2. **Generates embeddings** (line 170)
   - `generate_trial_embeddings()` checks each trial:
     - If embedding file exists (`trial_{trial_id}.npy`) → **SKIPS** (existing trial)
     - If embedding file doesn't exist → **GENERATES** (new trial)
   - **Only generates embeddings for NEW trials**

3. **Saves embeddings** (line 173)
   - `save_trial_embeddings()` receives only NEW embeddings
   - **CRITICAL BUG**: Creates FAISS index ONLY from NEW embeddings
   - **CRITICAL BUG**: Overwrites metadata.json with ONLY new trials
   - **CRITICAL BUG**: Overwrites FAISS index, losing all existing trials

## The Problem

**If you have 47 trials with embeddings and add 1 new trial:**

1. ✅ New trial gets embedding generated
2. ❌ FAISS index gets OVERWRITTEN with only the 1 new trial (loses 47 existing!)
3. ❌ metadata.json gets OVERWRITTEN with only the 1 new trial (loses 47 existing!)
4. ❌ Result: FAISS index now has 1 trial instead of 48!

## What Should Happen

**When new trials are added:**

1. ✅ New trials get embeddings generated
2. ✅ Load ALL existing embeddings from disk
3. ✅ Combine existing + new embeddings
4. ✅ Rebuild FAISS index with ALL embeddings
5. ✅ Update (merge) metadata.json with all trials
6. ✅ Result: FAISS index has all 48 trials (47 existing + 1 new)

## Current Status

- ✅ **Detects new trials correctly** (checks if embedding file exists)
- ✅ **Generates embeddings for new trials**
- ❌ **Does NOT combine with existing embeddings**
- ❌ **Overwrites FAISS index and metadata**
- ❌ **Loses all existing embeddings when saving**

## Fix Required

The `save_trial_embeddings()` method needs to:
1. Load existing embeddings and metadata
2. Merge new embeddings with existing ones
3. Rebuild FAISS index with ALL embeddings (existing + new)
4. Update metadata.json with ALL trials (merge, don't overwrite)

