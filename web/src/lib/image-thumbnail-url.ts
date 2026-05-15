export function getImageThumbnailUrl(src: string) {
  const marker = "/images/";
  const index = src.indexOf(marker);
  if (index < 0) return src;
  return `${src.slice(0, index)}/image-thumbnails/${src.slice(index + marker.length)}`;
}
