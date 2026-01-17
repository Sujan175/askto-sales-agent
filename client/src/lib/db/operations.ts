import { getInterviewsCollection } from './client';
import { InterviewDetails } from '../interview';

export interface SaveInterviewResponse {
    success: boolean;
    inserted_id?: string;
    error?: string;
}

/**
 * Save interview details to database
 * @param details Interview details to save
 * @param mongoUri MongoDB connection string
 * @returns Success status and inserted document ID
 */
export async function saveInterviewToDb(
    details: InterviewDetails,
    mongoUri: string
): Promise<SaveInterviewResponse> {
    const collection = await getInterviewsCollection(mongoUri);
    const result = await collection.insertOne(details);

    return {
        success: true,
        inserted_id: result.insertedId.toString(),
    };
}

/**
 * Get interview by session ID
 * @param sessionId Session ID to search for
 * @param mongoUri MongoDB connection string
 * @returns Interview details or null if not found
 */
export async function getInterviewBySessionId(
    sessionId: string,
    mongoUri: string
): Promise<InterviewDetails | null> {
    const collection = await getInterviewsCollection(mongoUri);
    const result = await collection.findOne({ session_id: sessionId });

    return result as InterviewDetails | null;
}
