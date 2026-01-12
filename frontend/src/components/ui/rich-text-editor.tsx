import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import { TextStyle } from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import Highlight from '@tiptap/extension-highlight';
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Link as LinkIcon,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Heading1,
  Heading2,
  Code,
  Quote,
  Undo,
  Redo,
  Highlighter,
  Variable,
} from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Input } from './input';
import { useState } from 'react';

interface RichTextEditorProps {
  content: string;
  onChange: (html: string) => void;
  placeholder?: string;
  className?: string;
  variables?: Record<string, string[]>;
  onInsertVariable?: (variable: string) => void;
}

export function RichTextEditor({
  content,
  onChange,
  placeholder = 'Write your email content...',
  className,
  variables,
  onInsertVariable,
}: RichTextEditorProps) {
  const [linkUrl, setLinkUrl] = useState('');

  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 underline',
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Underline,
      TextStyle,
      Color,
      Highlight.configure({
        multicolor: true,
      }),
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] p-4',
      },
    },
  });

  if (!editor) {
    return null;
  }

  const setLink = () => {
    if (linkUrl) {
      editor.chain().focus().extendMarkRange('link').setLink({ href: linkUrl }).run();
      setLinkUrl('');
    } else {
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
    }
  };

  const insertVariable = (variable: string) => {
    editor.chain().focus().insertContent(`{{${variable}}}`).run();
    if (onInsertVariable) {
      onInsertVariable(variable);
    }
  };

  return (
    <div className={cn('border rounded-lg overflow-hidden', className)}>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-1 p-2 border-b bg-muted/50">
        {/* History */}
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
          className="h-8 w-8"
        >
          <Undo className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
          className="h-8 w-8"
        >
          <Redo className="h-4 w-4" />
        </Button>

        <div className="w-px h-6 bg-border mx-1" />

        {/* Text formatting */}
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={cn('h-8 w-8', editor.isActive('bold') && 'bg-accent')}
        >
          <Bold className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={cn('h-8 w-8', editor.isActive('italic') && 'bg-accent')}
        >
          <Italic className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          className={cn('h-8 w-8', editor.isActive('underline') && 'bg-accent')}
        >
          <UnderlineIcon className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleStrike().run()}
          className={cn('h-8 w-8', editor.isActive('strike') && 'bg-accent')}
        >
          <Strikethrough className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleHighlight().run()}
          className={cn('h-8 w-8', editor.isActive('highlight') && 'bg-accent')}
        >
          <Highlighter className="h-4 w-4" />
        </Button>

        <div className="w-px h-6 bg-border mx-1" />

        {/* Headings */}
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={cn('h-8 w-8', editor.isActive('heading', { level: 1 }) && 'bg-accent')}
        >
          <Heading1 className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={cn('h-8 w-8', editor.isActive('heading', { level: 2 }) && 'bg-accent')}
        >
          <Heading2 className="h-4 w-4" />
        </Button>

        <div className="w-px h-6 bg-border mx-1" />

        {/* Alignment */}
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().setTextAlign('left').run()}
          className={cn('h-8 w-8', editor.isActive({ textAlign: 'left' }) && 'bg-accent')}
        >
          <AlignLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().setTextAlign('center').run()}
          className={cn('h-8 w-8', editor.isActive({ textAlign: 'center' }) && 'bg-accent')}
        >
          <AlignCenter className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().setTextAlign('right').run()}
          className={cn('h-8 w-8', editor.isActive({ textAlign: 'right' }) && 'bg-accent')}
        >
          <AlignRight className="h-4 w-4" />
        </Button>

        <div className="w-px h-6 bg-border mx-1" />

        {/* Lists */}
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={cn('h-8 w-8', editor.isActive('bulletList') && 'bg-accent')}
        >
          <List className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={cn('h-8 w-8', editor.isActive('orderedList') && 'bg-accent')}
        >
          <ListOrdered className="h-4 w-4" />
        </Button>

        <div className="w-px h-6 bg-border mx-1" />

        {/* Quote and Code */}
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={cn('h-8 w-8', editor.isActive('blockquote') && 'bg-accent')}
        >
          <Quote className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          onClick={() => editor.chain().focus().toggleCode().run()}
          className={cn('h-8 w-8', editor.isActive('code') && 'bg-accent')}
        >
          <Code className="h-4 w-4" />
        </Button>

        <div className="w-px h-6 bg-border mx-1" />

        {/* Link */}
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              type="button"
              className={cn('h-8 w-8', editor.isActive('link') && 'bg-accent')}
            >
              <LinkIcon className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80">
            <div className="flex gap-2">
              <Input
                placeholder="Enter URL..."
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
              />
              <Button size="sm" onClick={setLink}>
                {linkUrl ? 'Set' : 'Remove'}
              </Button>
            </div>
          </PopoverContent>
        </Popover>

        {/* Variables */}
        {variables && Object.keys(variables).length > 0 && (
          <>
            <div className="w-px h-6 bg-border mx-1" />
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="sm" type="button" className="h-8 gap-1">
                  <Variable className="h-4 w-4" />
                  Variables
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 max-h-64 overflow-y-auto">
                <div className="space-y-3">
                  {Object.entries(variables).map(([category, vars]) => (
                    <div key={category}>
                      <div className="text-xs font-medium text-muted-foreground uppercase mb-1">
                        {category}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {vars.map((variable) => (
                          <Button
                            key={variable}
                            variant="outline"
                            size="sm"
                            type="button"
                            className="h-6 text-xs"
                            onClick={() => insertVariable(variable)}
                          >
                            {variable}
                          </Button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </PopoverContent>
            </Popover>
          </>
        )}
      </div>

      {/* Editor Content */}
      <EditorContent editor={editor} />
    </div>
  );
}
