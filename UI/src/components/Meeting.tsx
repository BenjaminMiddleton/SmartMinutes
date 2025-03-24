import React, { FunctionComponent, useState, useCallback } from "react";
import ButtonAttendee from "./ButtonAttendee";
import LockIcon from "./LockIcon";
import styles from "./Meeting.module.css";

export type MeetingProps = {
  className?: string;
  title: string;
  attendeeCount?: number;
};

const Meeting: FunctionComponent<MeetingProps> = ({
  className = "",
  title = "Meeting Title",
  attendeeCount = 1,
}) => {
  // Maintain state for lock icon
  const [isLocked, setIsLocked] = useState<boolean>(false);
  const [isRecordHovered, setIsRecordHovered] = useState<boolean>(false);
  const [isRecordPressed, setIsRecordPressed] = useState<boolean>(false);
  const [isRecordToggled, setIsRecordToggled] = useState<boolean>(false);

  // Handle record button mouse events
  const handleRecordMouseDown = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRecordPressed(true);
  }, []);

  const handleRecordMouseUp = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRecordPressed(false);
  }, []);
  
  // Handle record button click to toggle state
  const handleRecordClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRecordToggled(prev => !prev);
  }, []);

  return (
    <div className={[styles.title1, className].join(" ")}>
      {/* Time and Record Button Container */}
      <div className={styles.timeRecordContainer}>
        {/* Time Container */}
        <div className={styles.timeContainer}>
          <span className={styles.timeDisplay}>00:00</span>
        </div>
        {/* Record Button Container */}
        <div className={styles.recordButtonContainer}>
          <div 
            className={`${styles.recordButton} ${isRecordToggled ? styles.recordButtonToggled : ''}`}
            onMouseEnter={() => setIsRecordHovered(true)}
            onMouseLeave={() => {
              setIsRecordHovered(false);
              setIsRecordPressed(false);
            }}
            onMouseDown={handleRecordMouseDown}
            onMouseUp={handleRecordMouseUp}
            onClick={handleRecordClick}
          ></div>
        </div>
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

export default Meeting;