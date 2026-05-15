"use client";

import { useEffect, useMemo, useState } from "react";

import { getImageThumbnailUrl } from "@/lib/image-thumbnail-url";
import { cn } from "@/lib/utils";

export { getImageThumbnailUrl };

type ImageThumbnailProps = {
  src: string;
  thumbnailSrc?: string;
  alt?: string;
  className?: string;
  imageClassName?: string;
  onThumbnailLoad?: () => void;
  onThumbnailError?: () => void;
};

export function ImageThumbnail({ src, thumbnailSrc, alt = "", className, imageClassName, onThumbnailLoad, onThumbnailError }: ImageThumbnailProps) {
  const initialSrc = useMemo(() => thumbnailSrc || getImageThumbnailUrl(src), [src, thumbnailSrc]);
  const [currentSrc, setCurrentSrc] = useState(initialSrc);

  useEffect(() => {
    setCurrentSrc(initialSrc);
  }, [initialSrc]);

  return (
    <span className={cn("block overflow-hidden bg-stone-100", className)}>
      <img
        src={currentSrc}
        alt={alt}
        className={cn("h-full w-full object-cover", imageClassName)}
        loading="lazy"
        decoding="async"
        onLoad={() => {
          if (currentSrc !== src) {
            onThumbnailLoad?.();
          }
        }}
        onError={() => {
          if (currentSrc !== src) {
            onThumbnailError?.();
            setCurrentSrc(src);
          }
        }}
      />
    </span>
  );
}
