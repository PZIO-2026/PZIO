import { File as FileIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { getAttachmentObjectUrl } from "../api";
import type { Attachment } from "../types";

interface AttachmentPreviewProps {
  attachment: Attachment;
  className?: string;
  iconClassName?: string;
}

export default function AttachmentPreview({ attachment, className = "w-full h-full object-cover", iconClassName = "w-20 h-20 text-slate-400" }: AttachmentPreviewProps) {
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const isImage = attachment.contentType?.startsWith("image/");

  useEffect(() => {
    let url: string | null = null;
    if (isImage) {
      getAttachmentObjectUrl(attachment.attachmentId)
        .then((newUrl) => {
          url = newUrl;
          setImgSrc(url);
        })
        .catch(console.error);
    }
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [attachment.attachmentId, isImage]);

  if (imgSrc) {
    return <img src={imgSrc} alt={attachment.filename} className={className} />;
  }

  return <FileIcon className={iconClassName} />;
}
