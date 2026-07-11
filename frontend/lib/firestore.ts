import { initializeApp, getApps } from "firebase/app";
import {
  getFirestore,
  collection,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
  Timestamp,
  QuerySnapshot,
  DocumentData,
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

export function subscribeToReports(
  onData: (reports: Report[]) => void,
  onError?: (e: Error) => void
) {
  const db = getFirestore(getApp());
  const q = query(
    collection(db, "reports"),
    orderBy("timestamp", "desc"),
    limit(20)
  );

  return onSnapshot(
    q,
    (snap: QuerySnapshot<DocumentData>) => {
      const reports = snap.docs.map((d) => d.data() as Report);
      onData(reports);
    },
    (err) => {
      onError?.(err);
    }
  );
}

export function subscribeToReportsByPincode(
  pincode: string,
  onData: (reports: Report[]) => void,
  onError?: (e: Error) => void
) {
  const db = getFirestore(getApp());
  const q = query(
    collection(db, "reports"),
    where("pincode", "==", pincode),
    orderBy("timestamp", "desc"),
    limit(10)
  );

  return onSnapshot(
    q,
    (snap: QuerySnapshot<DocumentData>) => {
      const reports = snap.docs.map((d) => d.data() as Report);
      onData(reports);
    },
    (err) => {
      onError?.(err);
    }
  );
}
