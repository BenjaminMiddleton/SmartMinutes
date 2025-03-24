import React, { FunctionComponent, useState } from "react";
import ButtonAttendee from "./ButtonAttendee";
import LockIcon from "./LockIcon";
import styles from "./PastMeeting.module.css";

export type PastMeetingProps = {
  className?: string;
  title: string;
  attendeeCount?: number;
  completionDate?: string;
  status?: "completed" | "cancelled" | "missed";
  actualDuration?: string;
};

const PastMeeting: FunctionComponent<PastMeetingProps> = ({
  className = "",
  title = "Past Meeting",
  attendeeCount = 1,
  completionDate = "Unknown",
  status = "completed",
  actualDuration = "00:00",
}) => {
  // Maintain state for lock icon
  const [isLocked, setIsLocked] = useState<boolean>(false);

  return (
    <div className={[styles.title1, className].join(" ")}>
      {/* Time Container (using same structure as Meeting component) */}
      <div className={styles.timeRecordContainer}>
        {/* Time Container */}
        <div className={styles.timeContainer}>
          <span className={styles.timeDisplay}>00:00</span>
        </div>
        {/* No record button here, but keeping the container structure */}
      </div>
      
      <h4 className={styles.title}>{title}</h4>
      <div className={styles.lockattendees}>
        <LockIcon 
          className={styles.lockIcon} 
          isLocked={isLocked}
          onLockToggle={setIsLocked}
        />
        <ButtonAttendee count={attendeeCount} />
      </div>
    </div>
  );
};

export default PastMeeting;
