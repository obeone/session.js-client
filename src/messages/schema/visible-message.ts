import { SignalService } from '@session.js/types/signal-bindings'
import { ExpirableMessage, type ExpirableMessageParams } from '../expirable-message'

import type { Reaction } from '@/reactions'
import { serializeProfile, type Profile } from '@/profile'

interface AttachmentPointerCommon {
  contentType?: string;
  key?: Uint8Array;
  size?: number;
  thumbnail?: Uint8Array;
  digest?: Uint8Array;
  fileName?: string;
  flags?: number;
  width?: number;
  height?: number;
  caption?: string;
}

export interface AttachmentPointer extends AttachmentPointerCommon {
  url?: string;
  id?: number;
}

export interface AttachmentPointerWithUrl extends AttachmentPointerCommon {
  url: string;
  id: number;
}

export interface Preview {
  url: string;
  title?: string;
  image?: AttachmentPointer;
}

export interface PreviewWithAttachmentUrl {
  url: string;
  id: number;
  title?: string;
  image?: AttachmentPointerWithUrl;
}

interface QuotedAttachmentCommon {
  contentType?: string;
  fileName?: string;
}

export interface QuotedAttachment extends QuotedAttachmentCommon {
  thumbnail?: AttachmentPointer;
}

export interface QuotedAttachmentWithUrl extends QuotedAttachmentCommon {
  thumbnail?: AttachmentPointerWithUrl | QuotedAttachment;
}

export interface Quote {
  id: number;
  author: string;
  text?: string;
  attachments?: Array<QuotedAttachmentWithUrl>;
}

export interface VisibleMessageParams extends ExpirableMessageParams {
  attachments?: Array<AttachmentPointerWithUrl>;
  body?: string;
  quote?: Quote;
  profile?: Profile;
  preview?: Array<PreviewWithAttachmentUrl>;
  reaction?: Reaction;
  syncTarget?: string; // undefined means it is not a synced message
}

export class VisibleMessage extends ExpirableMessage {
  public readonly reaction?: Reaction

  private readonly attachments?: Array<AttachmentPointerWithUrl>
  private readonly body?: string
  private readonly quote?: Quote
  private readonly profileKey?: Uint8Array
  private readonly profile?: SignalService.DataMessage.ILokiProfile
  private readonly preview?: Array<PreviewWithAttachmentUrl>

  private readonly syncTarget?: string

  constructor(params: VisibleMessageParams) {
    super({
      timestamp: params.timestamp,
      identifier: params.identifier,
      expirationType: params.expirationType,
      expireTimer: params.expireTimer,
    })
    this.attachments = params.attachments
    this.body = params.body
    this.quote = params.quote

    if (params.profile) {
      const profile = serializeProfile(params.profile)
      this.profile = profile.lokiProfile
      this.profileKey = profile.profileKey
    }

    this.preview = params.preview
    this.reaction = params.reaction
    this.syncTarget = params.syncTarget
  }

  public contentProto(): SignalService.Content {
    const content = super.contentProto()
    content.dataMessage = this.dataProto()
    return content
  }

  public dataProto(): SignalService.DataMessage {
    const dataMessage = super.dataProto()

    if (this.body) {
      dataMessage.body = this.body
    }

    dataMessage.attachments = this.attachments || []

    if (this.preview) {
      dataMessage.preview = this.preview
    }
    if (this.reaction) {
      dataMessage.reaction = this.reaction
    }
    if (this.syncTarget) {
      dataMessage.syncTarget = this.syncTarget
    }

    if (this.profile) {
      dataMessage.profile = this.profile
    }

    if (this.profileKey && this.profileKey.length) {
      dataMessage.profileKey = this.profileKey
    }

    if (this.quote) {
      dataMessage.quote = new SignalService.DataMessage.Quote()

      dataMessage.quote.id = this.quote.id
      dataMessage.quote.author = this.quote.author
      dataMessage.quote.text = this.quote.text
      if (this.quote.attachments) {
        dataMessage.quote.attachments = this.quote.attachments.map(attachment => {
          const quotedAttachment = new SignalService.DataMessage.Quote.QuotedAttachment()
          if (attachment.contentType) {
            quotedAttachment.contentType = attachment.contentType
          }
          if (attachment.fileName) {
            quotedAttachment.fileName = attachment.fileName
          }
          if (attachment.thumbnail && (attachment.thumbnail as any).id) {
            quotedAttachment.thumbnail = attachment.thumbnail as any
          }

          return quotedAttachment
        })
      }
    }

    if (Array.isArray(this.preview)) {
      dataMessage.preview = this.preview.map(preview => {
        const item = new SignalService.DataMessage.Preview()
        if (preview.title) {
          item.title = preview.title
        }
        if (preview.url) {
          item.url = preview.url
        }
        item.image = preview.image || null

        return item
      })
    }

    dataMessage.timestamp = this.timestamp

    return dataMessage
  }

  public isEqual(comparator: VisibleMessage): boolean {
    return this.identifier === comparator.identifier && this.timestamp === comparator.timestamp
  }
}