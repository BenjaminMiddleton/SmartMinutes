import React, { FunctionComponent, useState, useCallback } from "react";

export type LockIconProps = {
  className?: string;
  isLocked?: boolean;
  onLockToggle?: (isLocked: boolean) => void;
};

const LockIcon: FunctionComponent<LockIconProps> = ({
  className = "",
  isLocked = false,
  onLockToggle
}) => {
  // Maintain state for lock icon
  const [isLockClicked, setIsLockClicked] = useState<boolean>(isLocked);
  const [isLockHovered, setIsLockHovered] = useState<boolean>(false);
  const [hasMouseLeftSinceClick, setHasMouseLeftSinceClick] = useState<boolean>(false);

  // Handle lock icon click
  const handleLockClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent parent events from triggering
    const newLockState = !isLockClicked;
    setIsLockClicked(newLockState);
    setHasMouseLeftSinceClick(false); // Reset the state when clicked
    
    // Call the callback if provided
    if (onLockToggle) {
      onLockToggle(newLockState);
    }
  }, [isLockClicked, onLockToggle]);

  // Handle mouse enter for lock icon
  const handleLockMouseEnter = useCallback(() => {
    setIsLockHovered(true);
  }, []);

  // Handle mouse leave for lock icon
  const handleLockMouseLeave = useCallback(() => {
    setIsLockHovered(false);
    setHasMouseLeftSinceClick(true); // Set to true when mouse leaves
  }, []);

  return (
    <>
      {isLockClicked ? (
        isLockHovered && hasMouseLeftSinceClick ? (
          // Press > Hover state (only after mouse has left and returned)
          <svg 
            width="26" 
            height="34" 
            viewBox="0 0 26 34" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className={className}
            onClick={handleLockClick}
            onMouseEnter={handleLockMouseEnter}
            onMouseLeave={handleLockMouseLeave}
          > 
            <path d="M22.75 10.2002H21.125H17.875C14 11.5002 17.4801 10.5003 13 10.5003C8.51988 10.5003 11 12.0003 8.125 10.2002H4.875H3.25C2.38805 10.2002 1.5614 10.5584 0.951903 11.196C0.34241 11.8337 0 12.6985 0 13.6002V30.6002C0 31.5019 0.34241 32.3667 0.951903 33.0044C1.5614 33.642 2.38805 34.0002 3.25 34.0002H22.75C23.612 34.0002 24.4386 33.642 25.0481 33.0044C25.6576 32.3667 26 31.5019 26 30.6002V13.6002C26 12.6985 25.6576 11.8337 25.0481 11.196C24.4386 10.5584 23.612 10.2002 22.75 10.2002ZM14.625 23.3293V27.2002H11.375V23.3293C10.4081 22.7411 9.75 21.6565 9.75 20.4002C9.75 19.4985 10.0924 18.6337 10.7019 17.996C11.3114 17.3584 12.138 17.0002 13 17.0002C13.862 17.0002 14.6886 17.3584 15.2981 17.996C15.9076 18.6337 16.25 19.4985 16.25 20.4002C16.25 21.6548 15.5919 22.7394 14.625 23.3293Z" fill="#A2A2A2"/> 
            <path d="M3.25 10.0456H17.875V8.09524C17.6989 6.69512 17.3629 6.03605 16.5229 4.95051C15.575 4.00607 14.3491 3.38683 12.9949 3.38683C11.6408 3.38683 10.6836 3.98438 10.0977 4.41406C9.68359 4.75391 9.0439 5.26711 8.51643 6.49788L5.39453 5.50781C6.21893 3.4631 6.8221 2.9588 7.7333 2.03008C9.00371 0.908617 10.6071 0.0499892 13 1.10515e-06C15.2468 -0.00107826 17.1632 0.788477 18.7492 2.36867C20.3352 3.94886 21.1272 5.85772 21.125 8.09524V10.0456H22.75C23.6437 10.0456 24.4091 10.363 25.0461 10.9976C25.6831 11.6323 26.0011 12.3943 26 13.2837H25.5C25.5 14.1742 25.182 14.9368 24.5461 15.5714C23.9102 16.2061 24.3948 12.2134 23.5 12.2123H4C3.10625 12.2123 2.54692 17.1336 1.911 16.5C1.27508 15.8664 0.956583 15.1038 0.9555 14.2123L0 13.2837C0 12.3932 0.3185 11.6312 0.9555 10.9976C1.5925 10.364 2.35733 10.0467 3.25 10.0456Z" fill="#A2A2A2"/> 
          </svg>
        ) : (
          // Press state (stays this way until mouse leaves and returns)
          <svg 
            width="26"
            height="34" 
            viewBox="0 0 26.15 34" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className={className}
            onClick={handleLockClick}
            onMouseEnter={handleLockMouseEnter}
            onMouseLeave={handleLockMouseLeave}
          >
            <path 
              d="m 25.196304,11.1958 c 0.6131,0.6377 0.9575,1.5025 0.9575,2.4042 v 17 c 0,0.9017 -0.3444,1.7665 -0.9575,2.4042 -0.6131,0.6376 -1.4446,0.9958 -2.3117,0.9958 H 3.269234 c -0.86706,0 -1.6986,-0.3582 -2.3117,-0.9958 C 0.344434,32.3665 0,31.5017 0,30.6 v -17 C 0,12.6983 0.344434,11.8335 0.957534,11.1958 1.570634,10.5582 2.402174,10.2 3.269234,10.2 h 1.63461 V 8.5 c 0,-4.6869 3.66644,-8.5 8.17306,-8.5 4.5067,0 8.1731,3.8131 8.1731,8.5 v 1.7 h 1.6346 c 0.8671,0 1.6986,0.3582 2.3117,0.9958 z M 8.173074,10.2 h 9.80773 V 8.5 c 0,-2.8118 -2.2002,-5.1 -4.9039,-5.1 -2.7036,0 -4.90383,2.2882 -4.90383,5.1 z m 8.17303,10.2 c 0,-0.9017 -0.3444,-1.7665 -0.9575,-2.4042 -0.6131,-0.6376 -1.4446,-0.9958 -2.3117,-0.9958 -0.867,0 -1.6986,0.3582 -2.3117,0.9958 -0.6131,0.6377 -0.9575,1.5025 -0.9575,2.4042 0,1.2563 0.662,2.3409 1.6346,2.9291 V 27.2 h 3.2692 v -3.8709 c 0.9726,-0.5899 1.6346,-1.6745 1.6346,-2.9291 z"
              fill="#838383"
            />
          </svg>
        )
      ) : (
        isLockHovered && hasMouseLeftSinceClick ? (
          // Default > Hover state (only after mouse has left and returned)
          <svg 
            width="26"
            height="34" 
            viewBox="0 0 26.15 34" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className={className}
            onClick={handleLockClick}
            onMouseEnter={handleLockMouseEnter}
            onMouseLeave={handleLockMouseLeave}
          >
            <path 
              d="m 25.196304,11.1958 c 0.6131,0.6377 0.9575,1.5025 0.9575,2.4042 v 17 c 0,0.9017 -0.3444,1.7665 -0.9575,2.4042 -0.6131,0.6376 -1.4446,0.9958 -2.3117,0.9958 H 3.269234 c -0.86706,0 -1.6986,-0.3582 -2.3117,-0.9958 C 0.344434,32.3665 0,31.5017 0,30.6 v -17 C 0,12.6983 0.344434,11.8335 0.957534,11.1958 1.570634,10.5582 2.402174,10.2 3.269234,10.2 h 1.63461 V 8.5 c 0,-4.6869 3.66644,-8.5 8.17306,-8.5 4.5067,0 8.1731,3.8131 8.1731,8.5 v 1.7 h 1.6346 c 0.8671,0 1.6986,0.3582 2.3117,0.9958 z M 8.173074,10.2 h 9.80773 V 8.5 c 0,-2.8118 -2.2002,-5.1 -4.9039,-5.1 -2.7036,0 -4.90383,2.2882 -4.90383,5.1 z m 8.17303,10.2 c 0,-0.9017 -0.3444,-1.7665 -0.9575,-2.4042 -0.6131,-0.6376 -1.4446,-0.9958 -2.3117,-0.9958 -0.867,0 -1.6986,0.3582 -2.3117,0.9958 -0.6131,0.6377 -0.9575,1.5025 -0.9575,2.4042 0,1.2563 0.662,2.3409 1.6346,2.9291 V 27.2 h 3.2692 v -3.8709 c 0.9726,-0.5899 1.6346,-1.6745 1.6346,-2.9291 z"
              fill="#A2A2A2"
            />
          </svg>
        ) : (
          // Default state (stays this way until mouse leaves and returns)
          <svg 
            width="26" 
            height="34" 
            viewBox="0 0 26 34" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className={className}
            onClick={handleLockClick}
            onMouseEnter={handleLockMouseEnter}
            onMouseLeave={handleLockMouseLeave}
          > 
            <path d="M22.75 10.2002H21.125H17.875C14 11.5002 17.4801 10.5003 13 10.5003C8.51988 10.5003 11 12.0003 8.125 10.2002H4.875H3.25C2.38805 10.2002 1.5614 10.5584 0.951903 11.196C0.34241 11.8337 0 12.6985 0 13.6002V30.6002C0 31.5019 0.34241 32.3667 0.951903 33.0044C1.5614 33.642 2.38805 34.0002 3.25 34.0002H22.75C23.612 34.0002 24.4386 33.642 25.0481 33.0044C25.6576 32.3667 26 31.5019 26 30.6002V13.6002C26 12.6985 25.6576 11.8337 25.0481 11.196C24.4386 10.5584 23.612 10.2002 22.75 10.2002ZM14.625 23.3293V27.2002H11.375V23.3293C10.4081 22.7411 9.75 21.6565 9.75 20.4002C9.75 19.4985 10.0924 18.6337 10.7019 17.996C11.3114 17.3584 12.138 17.0002 13 17.0002C13.862 17.0002 14.6886 17.3584 15.2981 17.996C15.9076 18.6337 16.25 19.4985 16.25 20.4002C16.25 21.6548 15.5919 22.7394 14.625 23.3293Z" fill="#F8F8F8"/> 
            <path d="M3.25 10.0456H17.875V8.09524C17.6989 6.69512 17.3629 6.03605 16.5229 4.95051C15.575 4.00607 14.3491 3.38683 12.9949 3.38683C11.6408 3.38683 10.6836 3.98438 10.0977 4.41406C9.68359 4.75391 9.0439 5.26711 8.51643 6.49788L5.39453 5.50781C6.21893 3.4631 6.8221 2.9588 7.7333 2.03008C9.00371 0.908617 10.6071 0.0499892 13 1.10515e-06C15.2468 -0.00107826 17.1632 0.788477 18.7492 2.36867C20.3352 3.94886 21.1272 5.85772 21.125 8.09524V10.0456H22.75C23.6437 10.0456 24.4091 10.363 25.0461 10.9976C25.6831 11.6323 26.0011 12.3943 26 13.2837H25.5C25.5 14.1742 25.182 14.9368 24.5461 15.5714C23.9102 16.2061 24.3948 12.2134 23.5 12.2123H4C3.10625 12.2123 2.54692 17.1336 1.911 16.5C1.27508 15.8664 0.956583 15.1038 0.9555 14.2123L0 13.2837C0 12.3932 0.3185 11.6312 0.9555 10.9976C1.5925 10.364 2.35733 10.0467 3.25 10.0456Z" fill="#F8F8F8"/> 
          </svg>
        )
      )}
    </>
  );
};

export default LockIcon;
