import { MongoClient, Db, Collection } from 'mongodb';

let client: MongoClient | null = null;
let db: Db | null = null;

/**
 * Initialize MongoDB client connection
 * @param mongoUri MongoDB connection string
 * @returns Database instance
 */
export async function initializeMongoClient(mongoUri: string): Promise<Db> {
    if (db) {
        return db;
    }

    if (!client) {
        console.log('Initializing MongoDB client...');
        try {
            client = new MongoClient(mongoUri, {
                connectTimeoutMS: 5000,
                socketTimeoutMS: 5000,
                maxPoolSize: 1,
                serverSelectionTimeoutMS: 5000,
            } as any);
            await client.connect();
            console.log('MongoDB client connected successfully');
        } catch (error) {
            console.error('Failed to connect to MongoDB:', error);
            throw error;
        }
    }
    
    db = client.db('askto_db');

    return db;
}

/**
 * Get the interviews collection
 * @param mongoUri MongoDB connection string
 * @returns Interviews collection
 */
export async function getInterviewsCollection(mongoUri: string): Promise<Collection> {
    const database = await initializeMongoClient(mongoUri);
    return database.collection('interviews');
}

/**
 * Close MongoDB connection
 */
export async function closeMongoClient(): Promise<void> {
    if (client) {
        await client.close();
        client = null;
        db = null;
    }
}
