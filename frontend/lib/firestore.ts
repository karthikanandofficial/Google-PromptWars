import { initializeApp, getApps } from "firebase/app";
import {
  getFirestore,
  collection,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
  QueryConstraint,
  QuerySnapshot,
  DocumentData,
  Unsubscribe,
} from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

function getApp() {
  if (!getApps().length) {
    return initializeApp(firebaseConfig);
  }
  return getApps()[0];
}

export interface Report {
  report_id: string;
  pincode: string;
  text: string;
  timestamp: string;
  source: string;
}

/** Open a real-time listener on the reports collection with the given constraints. */
function subscribe(
  constraints: QueryConstraint[],
  onData: (reports: Report[]) => void,
  onError?: (e: Error) => void
): Unsubscribe {
  const db = getFirestore(getApp());
  const q = query(collection(db, "reports"), ...constraints);

  return onSnapshot(
    q,
    (snap: QuerySnapshot<DocumentData>) => {
      onData(snap.docs.map((d) => d.data() as Report));
    },
    (err) => {
      onError?.(err);
    }
  );
}

/** Subscribe to the 20 most recent reports across all pincodes (map page feed). */
export function subscribeToReports(
  onData: (reports: Report[]) => void,
  onError?: (e: Error) => void
): Unsubscribe {
  return subscribe([orderBy("timestamp", "desc"), limit(20)], onData, onError);
}

/** Subscribe to the 10 most recent reports for a single pincode. */
export function subscribeToReportsByPincode(
  pincode: string,
  onData: (reports: Report[]) => void,
  onError?: (e: Error) => void
): Unsubscribe {
  return subscribe(
    [where("pincode", "==", pincode), orderBy("timestamp", "desc"), limit(10)],
    onData,
    onError
  );
}
