import { twMerge } from 'tailwind-merge';

type TypographyVariant = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p' | 'lead' | 'large' | 'small' | 'muted' | 'label';

interface TypographyProps extends React.HTMLAttributes<HTMLElement> {
    variant?: TypographyVariant;
    as?: React.ElementType;
    children: React.ReactNode;
}

const variants: Record<TypographyVariant, string> = {
    h1: "scroll-m-20 text-4xl font-bold tracking-tight lg:text-5xl",
    h2: "scroll-m-20 border-b border-border pb-2 text-3xl font-medium tracking-tight first:mt-0",
    h3: "scroll-m-20 text-2xl font-medium tracking-tight",
    h4: "scroll-m-20 text-xl font-medium tracking-tight",
    h5: "scroll-m-20 text-lg font-semibold tracking-tight",
    h6: "scroll-m-20 text-base font-semibold tracking-tight",
    p: "leading-7 [&:not(:first-child)]:mt-6",
    lead: "text-xl text-text-muted",
    large: "text-lg font-semibold",
    small: "text-sm font-medium leading-none",
    muted: "text-sm text-text-muted",
    label: "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
};

const defaultTags: Record<TypographyVariant, React.ElementType> = {
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    h4: 'h4',
    h5: 'h5',
    h6: 'h6',
    p: 'p',
    lead: 'p',
    large: 'div',
    small: 'small',
    muted: 'p',
    label: 'label'
};

export function Typography({
    variant = 'p',
    as,
    className,
    children,
    ...props
}: TypographyProps) {
    const Component = as || defaultTags[variant];

    return (
        <Component
            className={twMerge(variants[variant], "text-text-primary", className)}
            {...props}
        >
            {children}
        </Component>
    );
}
