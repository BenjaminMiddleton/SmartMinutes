import React, { FunctionComponent, useState } from "react";
import ButtonAttendee from "./ButtonAttendee";
import LockIcon from "./LockIcon";
import styles from "./MeetingTitle.module.css";

export type MeetingTitleProps = {
  className?: string;
  title: string;
  attendeeCount?: number;
};

const MeetingTitle: FunctionComponent<MeetingTitleProps> = ({
  className = "",
  title = "Meeting Title",
  attendeeCount = 1,
}) => {
  // Maintain state for lock icon
  const [isLocked, setIsLocked] = useState<boolean>(false);

  return (
    <div className={[styles.title1, className].join(" ")}>
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

export default MeetingTitle;
