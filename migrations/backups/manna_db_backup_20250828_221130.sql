--
-- PostgreSQL database dump
--

-- Dumped from database version 16.6
-- Dumped by pg_dump version 16.6

-- Started on 2025-08-28 22:11:30

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE IF EXISTS manna_db;
--
-- TOC entry 5422 (class 1262 OID 59917)
-- Name: manna_db; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE manna_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';


ALTER DATABASE manna_db OWNER TO postgres;

\connect manna_db

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 953 (class 1247 OID 60350)
-- Name: dayofweekenum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.dayofweekenum AS ENUM (
    'sunday',
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday'
);


ALTER TYPE public.dayofweekenum OWNER TO postgres;

--
-- TOC entry 917 (class 1247 OID 60088)
-- Name: messagepriority; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.messagepriority AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'URGENT'
);


ALTER TYPE public.messagepriority OWNER TO postgres;

--
-- TOC entry 914 (class 1247 OID 60079)
-- Name: messagetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.messagetype AS ENUM (
    'ANNOUNCEMENT',
    'EVENT',
    'PRAYER_REQUEST',
    'GENERAL'
);


ALTER TYPE public.messagetype OWNER TO postgres;

--
-- TOC entry 977 (class 1247 OID 68908)
-- Name: paymentmethodstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.paymentmethodstatus AS ENUM (
    'PENDING',
    'VERIFIED',
    'FAILED',
    'EXPIRED'
);


ALTER TYPE public.paymentmethodstatus OWNER TO postgres;

--
-- TOC entry 974 (class 1247 OID 68898)
-- Name: paymentmethodtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.paymentmethodtype AS ENUM (
    'CARD',
    'ACH',
    'APPLE_PAY',
    'GOOGLE_PAY'
);


ALTER TYPE public.paymentmethodtype OWNER TO postgres;

--
-- TOC entry 986 (class 1247 OID 68944)
-- Name: transactionstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.transactionstatus AS ENUM (
    'PENDING',
    'PROCESSING',
    'SUCCEEDED',
    'FAILED',
    'CANCELLED',
    'REFUNDED'
);


ALTER TYPE public.transactionstatus OWNER TO postgres;

--
-- TOC entry 983 (class 1247 OID 68936)
-- Name: transactiontype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.transactiontype AS ENUM (
    'ROUNDUP',
    'MANUAL',
    'RECURRING'
);


ALTER TYPE public.transactiontype OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 233 (class 1259 OID 60207)
-- Name: access_codes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.access_codes (
    id integer NOT NULL,
    user_id integer NOT NULL,
    access_code character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone
);


ALTER TABLE public.access_codes OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 60206)
-- Name: access_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.access_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.access_codes_id_seq OWNER TO postgres;

--
-- TOC entry 5423 (class 0 OID 0)
-- Dependencies: 232
-- Name: access_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.access_codes_id_seq OWNED BY public.access_codes.id;


--
-- TOC entry 217 (class 1259 OID 60009)
-- Name: admin_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admin_users (
    id integer NOT NULL,
    email character varying NOT NULL,
    password character varying NOT NULL,
    is_superadmin boolean,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    role character varying,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    permissions character varying,
    last_login timestamp with time zone
);


ALTER TABLE public.admin_users OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 60008)
-- Name: admin_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.admin_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_users_id_seq OWNER TO postgres;

--
-- TOC entry 5424 (class 0 OID 0)
-- Dependencies: 216
-- Name: admin_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.admin_users_id_seq OWNED BY public.admin_users.id;


--
-- TOC entry 215 (class 1259 OID 60003)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- TOC entry 261 (class 1259 OID 69023)
-- Name: analytics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.analytics (
    id integer NOT NULL,
    analytics_type character varying(50) NOT NULL,
    scope_id integer,
    scope_type character varying(50),
    analytics_date timestamp with time zone NOT NULL,
    period_start timestamp with time zone,
    period_end timestamp with time zone,
    total_amount double precision DEFAULT 0.0,
    total_amount_cents integer DEFAULT 0,
    currency character varying(3) DEFAULT 'USD'::character varying,
    total_count integer DEFAULT 0,
    success_count integer DEFAULT 0,
    failure_count integer DEFAULT 0,
    growth_rate double precision DEFAULT 0.0,
    growth_percentage double precision DEFAULT 0.0,
    total_users integer DEFAULT 0,
    active_users integer DEFAULT 0,
    new_users integer DEFAULT 0,
    total_churches integer DEFAULT 0,
    active_churches integer DEFAULT 0,
    new_churches integer DEFAULT 0,
    total_transactions integer DEFAULT 0,
    successful_transactions integer DEFAULT 0,
    failed_transactions integer DEFAULT 0,
    average_transaction_value double precision DEFAULT 0.0,
    custom_metrics jsonb,
    description text,
    tags jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    legacy_model character varying(50),
    legacy_id integer
);


ALTER TABLE public.analytics OWNER TO postgres;

--
-- TOC entry 260 (class 1259 OID 69022)
-- Name: analytics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analytics_id_seq OWNER TO postgres;

--
-- TOC entry 5425 (class 0 OID 0)
-- Dependencies: 260
-- Name: analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.analytics_id_seq OWNED BY public.analytics.id;


--
-- TOC entry 219 (class 1259 OID 60021)
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    actor_type character varying,
    actor_id integer,
    action character varying,
    church_id integer,
    details_json json,
    created_at timestamp with time zone
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 60020)
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO postgres;

--
-- TOC entry 5426 (class 0 OID 0)
-- Dependencies: 218
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- TOC entry 235 (class 1259 OID 60222)
-- Name: bank_accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bank_accounts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    account_id character varying NOT NULL,
    name character varying,
    mask character varying,
    subtype character varying,
    type character varying,
    institution character varying,
    access_token character varying NOT NULL,
    created_at timestamp with time zone,
    is_active character varying(20) DEFAULT 'active'::character varying,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.bank_accounts OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 60221)
-- Name: bank_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bank_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bank_accounts_id_seq OWNER TO postgres;

--
-- TOC entry 5427 (class 0 OID 0)
-- Dependencies: 234
-- Name: bank_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bank_accounts_id_seq OWNED BY public.bank_accounts.id;


--
-- TOC entry 237 (class 1259 OID 60237)
-- Name: beneficial_owners; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.beneficial_owners (
    id integer NOT NULL,
    church_id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    middle_name character varying(100),
    date_of_birth date NOT NULL,
    ssn character varying(11) NOT NULL,
    email character varying(255),
    phone character varying(20),
    address_line_1 character varying(255) NOT NULL,
    address_line_2 character varying(255),
    city character varying(100) NOT NULL,
    state character varying(2) NOT NULL,
    zip_code character varying(10) NOT NULL,
    country character varying(2),
    id_type character varying(50) NOT NULL,
    id_number character varying(50) NOT NULL,
    id_issuing_country character varying(2),
    id_expiration_date date,
    id_front_url character varying(500),
    id_back_url character varying(500),
    ownership_percentage integer,
    title character varying(100),
    is_control_person boolean,
    is_verified boolean,
    verified_at timestamp with time zone,
    verified_by integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.beneficial_owners OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 60236)
-- Name: beneficial_owners_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.beneficial_owners_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.beneficial_owners_id_seq OWNER TO postgres;

--
-- TOC entry 5428 (class 0 OID 0)
-- Dependencies: 236
-- Name: beneficial_owners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.beneficial_owners_id_seq OWNED BY public.beneficial_owners.id;


--
-- TOC entry 239 (class 1259 OID 60258)
-- Name: church_admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.church_admins (
    id integer NOT NULL,
    user_id integer NOT NULL,
    church_id integer NOT NULL,
    role character varying,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    admin_name character varying(255),
    permissions json,
    is_primary_admin boolean DEFAULT false,
    can_manage_finances boolean DEFAULT true,
    can_manage_members boolean DEFAULT true,
    can_manage_settings boolean DEFAULT true,
    contact_email character varying(255),
    contact_phone character varying(50),
    admin_notes text,
    admin_metadata json,
    last_activity timestamp with time zone,
    stripe_identity_session_id character varying(255),
    identity_verification_status character varying(50) DEFAULT 'not_started'::character varying,
    identity_verification_date timestamp with time zone
);


ALTER TABLE public.church_admins OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 60257)
-- Name: church_admins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.church_admins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.church_admins_id_seq OWNER TO postgres;

--
-- TOC entry 5429 (class 0 OID 0)
-- Dependencies: 238
-- Name: church_admins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.church_admins_id_seq OWNED BY public.church_admins.id;


--
-- TOC entry 269 (class 1259 OID 69124)
-- Name: church_memberships; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.church_memberships (
    id integer NOT NULL,
    user_id integer NOT NULL,
    church_id integer NOT NULL,
    role character varying(20) DEFAULT 'member'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.church_memberships OWNER TO postgres;

--
-- TOC entry 268 (class 1259 OID 69123)
-- Name: church_memberships_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.church_memberships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.church_memberships_id_seq OWNER TO postgres;

--
-- TOC entry 5430 (class 0 OID 0)
-- Dependencies: 268
-- Name: church_memberships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.church_memberships_id_seq OWNED BY public.church_memberships.id;


--
-- TOC entry 223 (class 1259 OID 60098)
-- Name: church_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.church_messages (
    id integer NOT NULL,
    church_id integer NOT NULL,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    type public.messagetype,
    priority public.messagepriority,
    is_active boolean,
    is_published boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    published_at timestamp with time zone
);


ALTER TABLE public.church_messages OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 60097)
-- Name: church_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.church_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.church_messages_id_seq OWNER TO postgres;

--
-- TOC entry 5431 (class 0 OID 0)
-- Dependencies: 222
-- Name: church_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.church_messages_id_seq OWNED BY public.church_messages.id;


--
-- TOC entry 275 (class 1259 OID 69201)
-- Name: church_payouts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.church_payouts (
    id integer NOT NULL,
    church_id integer NOT NULL,
    stripe_transfer_id character varying(100) NOT NULL,
    amount_transferred numeric(10,2) NOT NULL,
    manna_fees numeric(10,2) DEFAULT 0.00 NOT NULL,
    net_amount numeric(10,2) NOT NULL,
    payout_period_start timestamp with time zone NOT NULL,
    payout_period_end timestamp with time zone NOT NULL,
    donor_count integer DEFAULT 0 NOT NULL,
    total_roundups_processed integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    transferred_at timestamp with time zone
);


ALTER TABLE public.church_payouts OWNER TO postgres;

--
-- TOC entry 274 (class 1259 OID 69200)
-- Name: church_payouts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.church_payouts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.church_payouts_id_seq OWNER TO postgres;

--
-- TOC entry 5432 (class 0 OID 0)
-- Dependencies: 274
-- Name: church_payouts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.church_payouts_id_seq OWNED BY public.church_payouts.id;


--
-- TOC entry 225 (class 1259 OID 60114)
-- Name: church_referrals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.church_referrals (
    id integer NOT NULL,
    referring_church_id integer NOT NULL,
    referred_church_id integer NOT NULL,
    referral_code character varying NOT NULL,
    payout_status character varying,
    payout_amount double precision,
    payout_date timestamp with time zone,
    stripe_transfer_id character varying,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    commission_rate numeric(5,4) DEFAULT 0.10 NOT NULL,
    total_commission_earned numeric(12,2) DEFAULT 0.00 NOT NULL,
    commission_paid boolean DEFAULT false NOT NULL,
    commission_period_months integer DEFAULT 12 NOT NULL,
    activated_at timestamp with time zone,
    expires_at timestamp with time zone
);


ALTER TABLE public.church_referrals OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 60113)
-- Name: church_referrals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.church_referrals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.church_referrals_id_seq OWNER TO postgres;

--
-- TOC entry 5433 (class 0 OID 0)
-- Dependencies: 224
-- Name: church_referrals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.church_referrals_id_seq OWNED BY public.church_referrals.id;


--
-- TOC entry 221 (class 1259 OID 60043)
-- Name: churches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.churches (
    id integer NOT NULL,
    name character varying NOT NULL,
    ein character varying,
    website character varying,
    phone character varying,
    address character varying,
    email character varying,
    kyc_status character varying,
    kyc_submitted_at timestamp with time zone,
    kyc_approved_at timestamp with time zone,
    kyc_approved_by integer,
    kyc_rejected_at timestamp with time zone,
    kyc_rejected_by integer,
    kyc_rejection_reason character varying,
    kyc_data text,
    articles_of_incorporation_url character varying,
    irs_letter_url character varying,
    bank_statement_url character varying,
    board_resolution_url character varying,
    documents text,
    tax_exempt boolean,
    anti_terrorism boolean,
    legitimate_entity boolean,
    consent_checks boolean,
    ownership_disclosed boolean,
    info_accurate boolean,
    referral_code character varying,
    is_active boolean NOT NULL,
    status character varying,
    stripe_account_id character varying,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    city character varying,
    state character varying,
    zip_code character varying,
    tax_id character varying,
    pastor_name character varying,
    pastor_email character varying,
    pastor_phone character varying,
    kyc_state character varying(50),
    charges_enabled boolean,
    payouts_enabled boolean,
    disabled_reason character varying,
    requirements_json json,
    verified_at timestamp with time zone,
    document_status json,
    document_notes json,
    document_requests json,
    legal_name character varying(255),
    address_line_1 character varying(255),
    address_line_2 character varying(255),
    country character varying(2),
    kyc_additional_data json,
    primary_purpose text,
    total_received numeric(12,2) DEFAULT 0.00 NOT NULL
);


ALTER TABLE public.churches OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 60042)
-- Name: churches_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.churches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.churches_id_seq OWNER TO postgres;

--
-- TOC entry 5434 (class 0 OID 0)
-- Dependencies: 220
-- Name: churches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.churches_id_seq OWNED BY public.churches.id;


--
-- TOC entry 253 (class 1259 OID 68861)
-- Name: consents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.consents (
    id integer NOT NULL,
    user_id integer NOT NULL,
    version character varying(50) NOT NULL,
    accepted_at timestamp with time zone DEFAULT now(),
    ip character varying(45),
    user_agent text,
    text_snapshot text
);


ALTER TABLE public.consents OWNER TO postgres;

--
-- TOC entry 252 (class 1259 OID 68860)
-- Name: consents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.consents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.consents_id_seq OWNER TO postgres;

--
-- TOC entry 5435 (class 0 OID 0)
-- Dependencies: 252
-- Name: consents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.consents_id_seq OWNED BY public.consents.id;


--
-- TOC entry 241 (class 1259 OID 60308)
-- Name: donation_batches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.donation_batches (
    id integer NOT NULL,
    user_id integer NOT NULL,
    total_amount double precision NOT NULL,
    processing_fees double precision,
    multiplier_applied character varying,
    status character varying,
    created_at timestamp with time zone,
    executed_at timestamp with time zone,
    church_id integer,
    stripe_charge_id character varying,
    payout_status character varying,
    payout_date timestamp with time zone,
    retry_attempts integer,
    last_retry_at timestamp with time zone,
    batch_type character varying,
    roundup_count integer,
    collection_date timestamp with time zone,
    stripe_payment_intent_id character varying
);


ALTER TABLE public.donation_batches OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 60307)
-- Name: donation_batches_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.donation_batches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.donation_batches_id_seq OWNER TO postgres;

--
-- TOC entry 5436 (class 0 OID 0)
-- Dependencies: 240
-- Name: donation_batches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.donation_batches_id_seq OWNED BY public.donation_batches.id;


--
-- TOC entry 243 (class 1259 OID 60328)
-- Name: donation_preferences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.donation_preferences (
    id integer NOT NULL,
    user_id integer,
    frequency character varying,
    multiplier character varying,
    church_id integer,
    pause boolean,
    cover_processing_fees boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    roundups_enabled boolean NOT NULL,
    minimum_roundup double precision NOT NULL,
    monthly_cap double precision,
    exclude_categories character varying,
    target_church_id integer
);


ALTER TABLE public.donation_preferences OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 60327)
-- Name: donation_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.donation_preferences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.donation_preferences_id_seq OWNER TO postgres;

--
-- TOC entry 5437 (class 0 OID 0)
-- Dependencies: 242
-- Name: donation_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.donation_preferences_id_seq OWNED BY public.donation_preferences.id;


--
-- TOC entry 245 (class 1259 OID 60366)
-- Name: donation_schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.donation_schedules (
    id integer NOT NULL,
    user_id integer,
    access_token character varying,
    amount double precision,
    day_of_week public.dayofweekenum,
    recipient_id character varying,
    status character varying,
    next_run timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.donation_schedules OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 60365)
-- Name: donation_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.donation_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.donation_schedules_id_seq OWNER TO postgres;

--
-- TOC entry 5438 (class 0 OID 0)
-- Dependencies: 244
-- Name: donation_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.donation_schedules_id_seq OWNED BY public.donation_schedules.id;


--
-- TOC entry 273 (class 1259 OID 69174)
-- Name: donor_payouts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.donor_payouts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    church_id integer NOT NULL,
    stripe_charge_id character varying(100) NOT NULL,
    amount_collected numeric(10,2) NOT NULL,
    fees_covered_by_donor numeric(10,2) DEFAULT 0.00 NOT NULL,
    net_amount numeric(10,2) NOT NULL,
    collection_period_start timestamp with time zone NOT NULL,
    collection_period_end timestamp with time zone NOT NULL,
    transaction_count integer DEFAULT 0 NOT NULL,
    roundup_multiplier_applied numeric(3,1),
    monthly_cap_applied numeric(10,2),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    processed_at timestamp with time zone
);


ALTER TABLE public.donor_payouts OWNER TO postgres;

--
-- TOC entry 272 (class 1259 OID 69173)
-- Name: donor_payouts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.donor_payouts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.donor_payouts_id_seq OWNER TO postgres;

--
-- TOC entry 5439 (class 0 OID 0)
-- Dependencies: 272
-- Name: donor_payouts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.donor_payouts_id_seq OWNED BY public.donor_payouts.id;


--
-- TOC entry 265 (class 1259 OID 69069)
-- Name: impact_stories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.impact_stories (
    id integer NOT NULL,
    church_id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    amount_used numeric(10,2) NOT NULL,
    category character varying(50) NOT NULL,
    status character varying(20),
    image_url character varying(500),
    published_date timestamp with time zone,
    people_impacted integer,
    events_held integer,
    items_purchased integer,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.impact_stories OWNER TO postgres;

--
-- TOC entry 264 (class 1259 OID 69068)
-- Name: impact_stories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.impact_stories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.impact_stories_id_seq OWNER TO postgres;

--
-- TOC entry 5440 (class 0 OID 0)
-- Dependencies: 264
-- Name: impact_stories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.impact_stories_id_seq OWNED BY public.impact_stories.id;


--
-- TOC entry 263 (class 1259 OID 69052)
-- Name: metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.metrics (
    id integer NOT NULL,
    metric_name character varying(100) NOT NULL,
    metric_key character varying(100) NOT NULL,
    metric_value double precision NOT NULL,
    metric_unit character varying(50),
    metric_type character varying(50) NOT NULL,
    metric_category character varying(50),
    scope_id integer,
    scope_type character varying(50),
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    context_data jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.metrics OWNER TO postgres;

--
-- TOC entry 262 (class 1259 OID 69051)
-- Name: metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.metrics_id_seq OWNER TO postgres;

--
-- TOC entry 5441 (class 0 OID 0)
-- Dependencies: 262
-- Name: metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.metrics_id_seq OWNED BY public.metrics.id;


--
-- TOC entry 257 (class 1259 OID 68918)
-- Name: payment_methods; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payment_methods (
    id integer NOT NULL,
    user_id integer NOT NULL,
    stripe_payment_method_id character varying(255) NOT NULL,
    type public.paymentmethodtype NOT NULL,
    status public.paymentmethodstatus,
    is_default boolean,
    card_brand character varying(50),
    card_last4 character varying(4),
    card_exp_month integer,
    card_exp_year integer,
    bank_name character varying(255),
    bank_account_type character varying(50),
    bank_account_last4 character varying(4),
    wallet_type character varying(50),
    payment_metadata text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.payment_methods OWNER TO postgres;

--
-- TOC entry 256 (class 1259 OID 68917)
-- Name: payment_methods_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payment_methods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payment_methods_id_seq OWNER TO postgres;

--
-- TOC entry 5442 (class 0 OID 0)
-- Dependencies: 256
-- Name: payment_methods_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payment_methods_id_seq OWNED BY public.payment_methods.id;


--
-- TOC entry 277 (class 1259 OID 69223)
-- Name: payout_allocations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payout_allocations (
    id integer NOT NULL,
    donor_payout_id integer NOT NULL,
    church_payout_id integer NOT NULL,
    allocated_amount numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.payout_allocations OWNER TO postgres;

--
-- TOC entry 276 (class 1259 OID 69222)
-- Name: payout_allocations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payout_allocations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payout_allocations_id_seq OWNER TO postgres;

--
-- TOC entry 5443 (class 0 OID 0)
-- Dependencies: 276
-- Name: payout_allocations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payout_allocations_id_seq OWNED BY public.payout_allocations.id;


--
-- TOC entry 227 (class 1259 OID 60149)
-- Name: payouts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payouts (
    id integer NOT NULL,
    church_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    currency character varying(3),
    status character varying(20),
    stripe_transfer_id character varying(255),
    stripe_account_id character varying(255),
    period_start timestamp with time zone,
    period_end timestamp with time zone,
    processed_at timestamp with time zone,
    failed_at timestamp with time zone,
    failure_reason text,
    description character varying(500),
    payout_metadata text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.payouts OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 60148)
-- Name: payouts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payouts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payouts_id_seq OWNER TO postgres;

--
-- TOC entry 5444 (class 0 OID 0)
-- Dependencies: 226
-- Name: payouts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payouts_id_seq OWNED BY public.payouts.id;


--
-- TOC entry 267 (class 1259 OID 69102)
-- Name: plaid_accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plaid_accounts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    plaid_item_id character varying(100) NOT NULL,
    plaid_access_token_encrypted text NOT NULL,
    account_id character varying(100) NOT NULL,
    account_name character varying(255),
    account_mask character varying(10),
    account_type character varying(20),
    institution_name character varying(255),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_synced timestamp with time zone
);


ALTER TABLE public.plaid_accounts OWNER TO postgres;

--
-- TOC entry 266 (class 1259 OID 69101)
-- Name: plaid_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.plaid_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.plaid_accounts_id_seq OWNER TO postgres;

--
-- TOC entry 5445 (class 0 OID 0)
-- Dependencies: 266
-- Name: plaid_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.plaid_accounts_id_seq OWNED BY public.plaid_accounts.id;


--
-- TOC entry 255 (class 1259 OID 68877)
-- Name: plaid_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plaid_items (
    id integer NOT NULL,
    user_id integer NOT NULL,
    item_id character varying(255) NOT NULL,
    access_token text NOT NULL,
    status character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.plaid_items OWNER TO postgres;

--
-- TOC entry 254 (class 1259 OID 68876)
-- Name: plaid_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.plaid_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.plaid_items_id_seq OWNER TO postgres;

--
-- TOC entry 5446 (class 0 OID 0)
-- Dependencies: 254
-- Name: plaid_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.plaid_items_id_seq OWNED BY public.plaid_items.id;


--
-- TOC entry 247 (class 1259 OID 60384)
-- Name: referral_commissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.referral_commissions (
    id integer NOT NULL,
    referral_id integer NOT NULL,
    church_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    commission_rate numeric(5,4) NOT NULL,
    base_amount numeric(10,2) NOT NULL,
    status character varying(20),
    paid_at timestamp with time zone,
    payout_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    church_referral_id integer,
    church_payout_id integer,
    commission_amount numeric(10,2),
    period_start character varying(20),
    period_end character varying(20)
);


ALTER TABLE public.referral_commissions OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 60383)
-- Name: referral_commissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.referral_commissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.referral_commissions_id_seq OWNER TO postgres;

--
-- TOC entry 5447 (class 0 OID 0)
-- Dependencies: 246
-- Name: referral_commissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.referral_commissions_id_seq OWNED BY public.referral_commissions.id;


--
-- TOC entry 229 (class 1259 OID 60167)
-- Name: referrals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.referrals (
    id integer NOT NULL,
    referring_church_id integer NOT NULL,
    referred_church_id integer NOT NULL,
    referral_code character varying(50) NOT NULL,
    commission_rate numeric(5,4),
    commission_amount numeric(10,2),
    status character varying(20),
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    activated_at timestamp with time zone,
    completed_at timestamp with time zone
);


ALTER TABLE public.referrals OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 60166)
-- Name: referrals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.referrals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.referrals_id_seq OWNER TO postgres;

--
-- TOC entry 5448 (class 0 OID 0)
-- Dependencies: 228
-- Name: referrals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.referrals_id_seq OWNED BY public.referrals.id;


--
-- TOC entry 249 (class 1259 OID 60408)
-- Name: refresh_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.refresh_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone,
    last_used timestamp with time zone,
    is_active boolean NOT NULL,
    device_info text,
    ip_address character varying,
    user_agent text,
    rotation_count integer NOT NULL,
    parent_token_id integer
);


ALTER TABLE public.refresh_tokens OWNER TO postgres;

--
-- TOC entry 248 (class 1259 OID 60407)
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.refresh_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.refresh_tokens_id_seq OWNER TO postgres;

--
-- TOC entry 5449 (class 0 OID 0)
-- Dependencies: 248
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.refresh_tokens_id_seq OWNED BY public.refresh_tokens.id;


--
-- TOC entry 271 (class 1259 OID 69148)
-- Name: roundup_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roundup_settings (
    id integer NOT NULL,
    user_id integer NOT NULL,
    church_id integer NOT NULL,
    collection_frequency character varying(20) DEFAULT 'bi_weekly'::character varying NOT NULL,
    roundup_multiplier numeric(3,1) DEFAULT 1.0 NOT NULL,
    monthly_cap numeric(10,2),
    cover_processing_fees boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.roundup_settings OWNER TO postgres;

--
-- TOC entry 270 (class 1259 OID 69147)
-- Name: roundup_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roundup_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roundup_settings_id_seq OWNER TO postgres;

--
-- TOC entry 5450 (class 0 OID 0)
-- Dependencies: 270
-- Name: roundup_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roundup_settings_id_seq OWNED BY public.roundup_settings.id;


--
-- TOC entry 259 (class 1259 OID 68992)
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    category character varying(50) NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying,
    amount_cents integer NOT NULL,
    currency character varying(3) DEFAULT 'USD'::character varying,
    user_id integer,
    church_id integer NOT NULL,
    payment_method_id integer,
    stripe_payment_intent_id character varying(255),
    stripe_charge_id character varying(255),
    stripe_transfer_id character varying(255),
    roundup_period_key character varying(255),
    roundup_multiplier numeric(3,1),
    roundup_base_amount integer,
    transaction_count integer,
    batch_id character varying(255),
    batch_type character varying(50),
    period_start timestamp with time zone,
    period_end timestamp with time zone,
    processing_fees_cents integer DEFAULT 0,
    failure_reason text,
    description text,
    transaction_metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    processed_at timestamp with time zone,
    failed_at timestamp with time zone,
    legacy_model character varying(50),
    legacy_id integer
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- TOC entry 258 (class 1259 OID 68991)
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_id_seq OWNER TO postgres;

--
-- TOC entry 5451 (class 0 OID 0)
-- Dependencies: 258
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- TOC entry 251 (class 1259 OID 60444)
-- Name: user_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_settings (
    id integer NOT NULL,
    user_id integer NOT NULL,
    notifications_enabled boolean,
    email_notifications boolean,
    sms_notifications boolean,
    push_notifications boolean,
    privacy_share_analytics boolean,
    privacy_share_profile boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    language character varying(10) DEFAULT 'en'::character varying,
    timezone character varying(50) DEFAULT 'UTC'::character varying,
    currency character varying(3) DEFAULT 'USD'::character varying,
    theme character varying(10) DEFAULT 'light'::character varying
);


ALTER TABLE public.user_settings OWNER TO postgres;

--
-- TOC entry 250 (class 1259 OID 60443)
-- Name: user_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_settings_id_seq OWNER TO postgres;

--
-- TOC entry 5452 (class 0 OID 0)
-- Dependencies: 250
-- Name: user_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_settings_id_seq OWNED BY public.user_settings.id;


--
-- TOC entry 231 (class 1259 OID 60186)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    first_name character varying NOT NULL,
    middle_name character varying,
    last_name character varying,
    email character varying,
    phone character varying,
    password character varying,
    is_email_verified boolean,
    is_phone_verified boolean,
    is_active boolean,
    role character varying,
    google_id character varying,
    apple_id character varying,
    church_id integer,
    stripe_customer_id character varying,
    profile_picture_url character varying,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    last_login timestamp with time zone,
    permissions text,
    password_hash text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 60185)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 5453 (class 0 OID 0)
-- Dependencies: 230
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 4926 (class 2604 OID 60210)
-- Name: access_codes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.access_codes ALTER COLUMN id SET DEFAULT nextval('public.access_codes_id_seq'::regclass);


--
-- TOC entry 4910 (class 2604 OID 60012)
-- Name: admin_users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_users ALTER COLUMN id SET DEFAULT nextval('public.admin_users_id_seq'::regclass);


--
-- TOC entry 4964 (class 2604 OID 69026)
-- Name: analytics id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analytics ALTER COLUMN id SET DEFAULT nextval('public.analytics_id_seq'::regclass);


--
-- TOC entry 4911 (class 2604 OID 60024)
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- TOC entry 4927 (class 2604 OID 60225)
-- Name: bank_accounts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank_accounts ALTER COLUMN id SET DEFAULT nextval('public.bank_accounts_id_seq'::regclass);


--
-- TOC entry 4930 (class 2604 OID 60240)
-- Name: beneficial_owners id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.beneficial_owners ALTER COLUMN id SET DEFAULT nextval('public.beneficial_owners_id_seq'::regclass);


--
-- TOC entry 4932 (class 2604 OID 60261)
-- Name: church_admins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_admins ALTER COLUMN id SET DEFAULT nextval('public.church_admins_id_seq'::regclass);


--
-- TOC entry 4994 (class 2604 OID 69127)
-- Name: church_memberships id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_memberships ALTER COLUMN id SET DEFAULT nextval('public.church_memberships_id_seq'::regclass);


--
-- TOC entry 4914 (class 2604 OID 60101)
-- Name: church_messages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_messages ALTER COLUMN id SET DEFAULT nextval('public.church_messages_id_seq'::regclass);


--
-- TOC entry 5011 (class 2604 OID 69204)
-- Name: church_payouts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_payouts ALTER COLUMN id SET DEFAULT nextval('public.church_payouts_id_seq'::regclass);


--
-- TOC entry 4916 (class 2604 OID 60117)
-- Name: church_referrals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_referrals ALTER COLUMN id SET DEFAULT nextval('public.church_referrals_id_seq'::regclass);


--
-- TOC entry 4912 (class 2604 OID 60046)
-- Name: churches id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.churches ALTER COLUMN id SET DEFAULT nextval('public.churches_id_seq'::regclass);


--
-- TOC entry 4952 (class 2604 OID 68864)
-- Name: consents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consents ALTER COLUMN id SET DEFAULT nextval('public.consents_id_seq'::regclass);


--
-- TOC entry 4938 (class 2604 OID 60311)
-- Name: donation_batches id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_batches ALTER COLUMN id SET DEFAULT nextval('public.donation_batches_id_seq'::regclass);


--
-- TOC entry 4939 (class 2604 OID 60331)
-- Name: donation_preferences id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_preferences ALTER COLUMN id SET DEFAULT nextval('public.donation_preferences_id_seq'::regclass);


--
-- TOC entry 4940 (class 2604 OID 60369)
-- Name: donation_schedules id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_schedules ALTER COLUMN id SET DEFAULT nextval('public.donation_schedules_id_seq'::regclass);


--
-- TOC entry 5006 (class 2604 OID 69177)
-- Name: donor_payouts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donor_payouts ALTER COLUMN id SET DEFAULT nextval('public.donor_payouts_id_seq'::regclass);


--
-- TOC entry 4988 (class 2604 OID 69072)
-- Name: impact_stories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_stories ALTER COLUMN id SET DEFAULT nextval('public.impact_stories_id_seq'::regclass);


--
-- TOC entry 4985 (class 2604 OID 69055)
-- Name: metrics id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metrics ALTER COLUMN id SET DEFAULT nextval('public.metrics_id_seq'::regclass);


--
-- TOC entry 4956 (class 2604 OID 68921)
-- Name: payment_methods id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_methods ALTER COLUMN id SET DEFAULT nextval('public.payment_methods_id_seq'::regclass);


--
-- TOC entry 5017 (class 2604 OID 69226)
-- Name: payout_allocations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payout_allocations ALTER COLUMN id SET DEFAULT nextval('public.payout_allocations_id_seq'::regclass);


--
-- TOC entry 4921 (class 2604 OID 60152)
-- Name: payouts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payouts ALTER COLUMN id SET DEFAULT nextval('public.payouts_id_seq'::regclass);


--
-- TOC entry 4990 (class 2604 OID 69105)
-- Name: plaid_accounts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plaid_accounts ALTER COLUMN id SET DEFAULT nextval('public.plaid_accounts_id_seq'::regclass);


--
-- TOC entry 4954 (class 2604 OID 68880)
-- Name: plaid_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plaid_items ALTER COLUMN id SET DEFAULT nextval('public.plaid_items_id_seq'::regclass);


--
-- TOC entry 4943 (class 2604 OID 60387)
-- Name: referral_commissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referral_commissions ALTER COLUMN id SET DEFAULT nextval('public.referral_commissions_id_seq'::regclass);


--
-- TOC entry 4923 (class 2604 OID 60170)
-- Name: referrals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals ALTER COLUMN id SET DEFAULT nextval('public.referrals_id_seq'::regclass);


--
-- TOC entry 4945 (class 2604 OID 60411)
-- Name: refresh_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('public.refresh_tokens_id_seq'::regclass);


--
-- TOC entry 4999 (class 2604 OID 69151)
-- Name: roundup_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roundup_settings ALTER COLUMN id SET DEFAULT nextval('public.roundup_settings_id_seq'::regclass);


--
-- TOC entry 4958 (class 2604 OID 68995)
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- TOC entry 4946 (class 2604 OID 60447)
-- Name: user_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_settings ALTER COLUMN id SET DEFAULT nextval('public.user_settings_id_seq'::regclass);


--
-- TOC entry 4925 (class 2604 OID 60189)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 5372 (class 0 OID 60207)
-- Dependencies: 233
-- Data for Name: access_codes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.access_codes (id, user_id, access_code, expires_at, created_at) FROM stdin;
\.


--
-- TOC entry 5356 (class 0 OID 60009)
-- Dependencies: 217
-- Data for Name: admin_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admin_users (id, email, password, is_superadmin, first_name, last_name, role, is_active, created_at, updated_at, permissions, last_login) FROM stdin;
3	admin@manna.com	$2b$12$3I9IWqLmeAXFOVDh8eCUFeDPn1GubRD9/fUOFH4LYceFQn1mAAnh.	t	Admin	User	admin	t	2025-08-12 00:03:35.890213-05	2025-08-18 18:46:02.053191-05	admin	2025-08-18 18:46:02.0526-05
\.


--
-- TOC entry 5354 (class 0 OID 60003)
-- Dependencies: 215
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
e0a118033a64
\.


--
-- TOC entry 5400 (class 0 OID 69023)
-- Dependencies: 261
-- Data for Name: analytics; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.analytics (id, analytics_type, scope_id, scope_type, analytics_date, period_start, period_end, total_amount, total_amount_cents, currency, total_count, success_count, failure_count, growth_rate, growth_percentage, total_users, active_users, new_users, total_churches, active_churches, new_churches, total_transactions, successful_transactions, failed_transactions, average_transaction_value, custom_metrics, description, tags, created_at, updated_at, legacy_model, legacy_id) FROM stdin;
\.


--
-- TOC entry 5358 (class 0 OID 60021)
-- Dependencies: 219
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_logs (id, actor_type, actor_id, action, church_id, details_json, created_at) FROM stdin;
271	system	0	CHURCH_ONBOARDING_SUBMITTED	\N	{"resource_type": "church", "resource_id": 48, "church_name": "Grace Community Church", "admin_email": "doingcode333@gmail.com", "kyc_status": "pending_review", "stripe_account_created": true}	2025-08-25 13:39:17.37669-05
272	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:20.566012-05
273	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:21.105453-05
274	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:22.096388-05
275	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:23.104457-05
276	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:24.043696-05
277	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:25.048193-05
278	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:26.050931-05
279	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:27.076477-05
280	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:28.065151-05
281	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:29.260658-05
282	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:30.069769-05
283	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:31.060069-05
284	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:32.069668-05
285	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:33.062146-05
286	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:34.077579-05
287	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:35.065734-05
288	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:36.142257-05
289	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:37.102478-05
290	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:38.045136-05
291	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:39.082454-05
292	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:40.047275-05
293	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:41.07552-05
294	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:42.138852-05
295	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:43.064366-05
296	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:44.065834-05
297	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:45.070811-05
298	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:46.068099-05
299	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:47.055303-05
300	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:48.062221-05
301	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:49.054426-05
302	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:50.095063-05
303	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:51.064712-05
304	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:52.075209-05
305	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:53.060521-05
306	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:54.048297-05
307	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:55.061901-05
308	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:56.063326-05
309	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:57.054739-05
310	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:58.050883-05
311	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:39:59.042058-05
312	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:00.057755-05
314	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:02.075368-05
316	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:04.063227-05
318	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:06.104386-05
320	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:08.045974-05
322	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:10.069459-05
324	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:12.056705-05
326	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:14.027961-05
313	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:01.057968-05
315	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:03.160657-05
317	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:05.082928-05
319	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:07.049845-05
321	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:09.078015-05
323	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:11.048773-05
325	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:13.070063-05
327	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:15.055835-05
328	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:16.06001-05
329	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:17.04203-05
330	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:18.057248-05
331	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:19.037404-05
332	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:20.094597-05
333	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:21.077814-05
334	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:22.096909-05
335	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:23.050915-05
336	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:24.071227-05
337	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:25.084474-05
338	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:26.066153-05
339	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:27.050631-05
340	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:28.076094-05
341	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:29.056574-05
342	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:30.063889-05
343	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:31.445843-05
344	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:32.076795-05
345	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:33.043208-05
346	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:34.104222-05
347	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:35.052033-05
348	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:36.07545-05
349	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:37.044941-05
350	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:38.046081-05
351	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:39.05825-05
352	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:40.064452-05
353	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:41.058199-05
354	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:42.049428-05
355	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:43.028792-05
356	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:44.060131-05
357	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:45.079368-05
358	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:46.061414-05
359	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:47.066835-05
360	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:48.062411-05
361	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:49.061554-05
363	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:51.039669-05
365	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:53.034938-05
367	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:55.049151-05
369	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:57.049483-05
371	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:59.088069-05
373	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:01.08721-05
375	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:03.07767-05
377	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:05.071753-05
379	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:07.061801-05
381	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:09.071712-05
383	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:11.08151-05
385	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:13.057614-05
362	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:50.151653-05
364	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:52.048571-05
366	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:54.056748-05
368	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:56.045377-05
370	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:40:58.093512-05
372	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:00.075264-05
374	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:02.079638-05
376	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:04.085247-05
378	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:06.11023-05
380	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:08.068913-05
382	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:10.070233-05
384	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:12.047182-05
386	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:14.095872-05
387	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:15.086941-05
388	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:16.054093-05
389	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:17.125458-05
390	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:18.076099-05
391	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:19.087076-05
392	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:20.078036-05
393	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:21.075936-05
394	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:41:22.047398-05
395	church_admin	48	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 48, "charges_enabled": true, "payouts_enabled": true}	2025-08-25 13:41:23.257713-05
396	system	0	CHURCH_ONBOARDING_COMPLETED	\N	{"resource_type": "church", "resource_id": 48, "church_name": "Grace Community Church", "admin_email": "doingcode333@gmail.com"}	2025-08-25 13:41:26.574381-05
397	system	0	CHURCH_ONBOARDING_SUBMITTED	\N	{"resource_type": "church", "resource_id": 49, "church_name": "First Test Church", "admin_email": "doingcode333@gmail.com", "kyc_status": "pending_review", "stripe_account_created": true}	2025-08-25 13:47:39.006684-05
398	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:41.988222-05
399	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:42.488687-05
400	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:43.67792-05
401	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:44.511929-05
402	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:45.43699-05
403	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:46.454763-05
404	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:47.53865-05
405	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:48.441693-05
406	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:49.449274-05
407	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:50.499543-05
408	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:51.469802-05
409	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:52.502319-05
410	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:53.489293-05
411	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:54.449755-05
412	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:55.447133-05
413	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:56.446382-05
414	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:57.443222-05
415	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:58.514039-05
417	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:00.512161-05
419	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:02.448952-05
421	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:04.472379-05
423	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:06.612972-05
425	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:08.447664-05
427	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:10.441804-05
429	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:12.475829-05
431	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:14.456549-05
433	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:16.46108-05
435	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:18.420249-05
437	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:20.436704-05
439	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:22.484005-05
441	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:24.438267-05
443	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:26.46628-05
445	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:28.49625-05
447	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:30.433803-05
449	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:32.480429-05
451	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:34.45672-05
453	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:36.491714-05
455	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:38.45369-05
457	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:40.448928-05
459	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:42.441512-05
461	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:44.451138-05
463	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:46.434307-05
465	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:48.481912-05
467	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:50.514036-05
469	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:52.497118-05
471	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:54.444598-05
473	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:56.481056-05
475	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:58.448691-05
477	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:00.452976-05
479	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:02.449747-05
481	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:04.45875-05
483	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:06.424578-05
485	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:08.438294-05
487	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:10.449143-05
489	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:12.495178-05
416	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:47:59.624871-05
418	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:01.637668-05
420	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:03.512639-05
422	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:05.519006-05
424	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:07.481867-05
426	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:09.49697-05
428	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:11.425685-05
430	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:13.494797-05
432	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:15.544104-05
434	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:17.458926-05
436	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:19.779398-05
438	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:21.468875-05
440	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:23.438141-05
442	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:25.430655-05
444	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:27.461331-05
446	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:29.512173-05
448	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:31.479092-05
450	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:33.428955-05
452	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:35.466017-05
454	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:37.484068-05
456	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:39.48913-05
458	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:41.441518-05
460	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:43.464442-05
462	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:45.449127-05
464	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:47.471682-05
466	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:49.502227-05
468	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:51.461009-05
470	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:53.428666-05
472	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:55.436965-05
474	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:57.438778-05
476	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:48:59.459572-05
478	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:01.447222-05
480	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:03.507252-05
482	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:05.444512-05
484	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:07.447328-05
486	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:09.431255-05
488	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:11.44719-05
490	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:13.454565-05
491	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:14.457293-05
492	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:15.456653-05
493	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:16.573373-05
494	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:17.478418-05
496	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:19.506137-05
498	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": true, "payouts_enabled": true}	2025-08-25 13:49:21.55262-05
500	system	0	CHURCH_ONBOARDING_SUBMITTED	\N	{"resource_type": "church", "resource_id": 50, "church_name": "Grace Community Church", "admin_email": "pastorif30yt@gracechurch.org", "kyc_status": "pending_review", "stripe_account_created": true}	2025-08-25 14:34:47.161345-05
502	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:50.692589-05
504	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:52.2325-05
506	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:54.290063-05
508	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:56.240585-05
510	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:58.26001-05
512	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:00.263699-05
514	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:02.266964-05
516	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:04.222884-05
518	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:06.252609-05
520	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:08.231362-05
522	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:10.317023-05
524	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:12.351756-05
526	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:14.271437-05
528	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:16.286811-05
530	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:18.316146-05
532	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:20.252216-05
534	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:22.236628-05
536	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:24.251583-05
538	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:26.23956-05
540	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:28.220227-05
542	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:30.254719-05
544	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:32.221147-05
546	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:34.23569-05
548	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:36.219875-05
550	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:38.255276-05
552	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:40.309165-05
554	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:42.241078-05
556	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:44.230663-05
558	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:46.224703-05
560	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:48.266992-05
562	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:50.236917-05
564	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:52.269718-05
566	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:54.248085-05
568	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:56.260713-05
570	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:58.267177-05
572	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:00.349013-05
574	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:02.266628-05
495	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:18.461856-05
497	church_admin	49	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 49, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 13:49:20.461659-05
499	system	0	CHURCH_ONBOARDING_COMPLETED	\N	{"resource_type": "church", "resource_id": 49, "church_name": "First Test Church", "admin_email": "doingcode333@gmail.com"}	2025-08-25 13:49:24.298777-05
501	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:50.173178-05
503	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:51.273619-05
505	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:53.281913-05
507	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:55.269337-05
509	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:57.286938-05
511	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:34:59.249812-05
513	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:01.267575-05
515	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:03.270933-05
517	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:05.264436-05
519	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:07.267508-05
521	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:09.306861-05
523	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:11.280769-05
525	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:13.249627-05
527	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:15.25906-05
529	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:17.244906-05
531	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:19.265717-05
533	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:21.246437-05
535	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:23.316466-05
537	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:25.269506-05
539	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:27.255041-05
541	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:29.250048-05
543	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:31.231942-05
545	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:33.257677-05
547	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:35.231865-05
549	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:37.284875-05
551	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:39.232493-05
553	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:41.314901-05
555	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:43.225349-05
557	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:45.210995-05
559	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:47.23289-05
561	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:49.234828-05
563	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:51.242256-05
565	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:53.26661-05
567	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:55.244533-05
569	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:57.249701-05
571	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:35:59.26904-05
573	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:01.264001-05
575	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:03.297812-05
576	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:04.228342-05
578	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:06.242956-05
580	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:08.240322-05
582	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:10.222093-05
584	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:12.232555-05
586	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:14.248047-05
577	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:05.271483-05
579	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:07.264006-05
581	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:09.333703-05
583	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:11.234338-05
585	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:13.23396-05
587	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:15.230111-05
588	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:16.263217-05
589	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:17.266855-05
590	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:18.241736-05
591	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:19.301047-05
592	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:20.284356-05
593	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:21.289202-05
594	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:22.25021-05
595	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:23.25748-05
596	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:24.239475-05
597	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:25.254239-05
598	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:26.249772-05
599	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:27.304022-05
600	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:28.247077-05
601	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:29.234861-05
602	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:30.290566-05
603	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:31.251151-05
604	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:32.256521-05
605	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:33.266344-05
606	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:34.291155-05
607	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:35.252312-05
608	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:36.319955-05
609	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:37.234018-05
610	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:38.265054-05
611	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:39.221211-05
612	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:40.298833-05
613	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:41.224742-05
614	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:42.284028-05
615	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:43.251788-05
616	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:44.225445-05
617	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:45.251561-05
618	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:46.246017-05
619	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:47.254729-05
620	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:48.256072-05
621	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:49.244777-05
622	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:50.301788-05
623	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:51.253624-05
625	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:53.249499-05
627	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:55.248421-05
629	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:57.316336-05
631	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:59.303137-05
633	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": true, "payouts_enabled": true}	2025-08-25 14:37:01.322476-05
624	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:52.240136-05
626	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:54.258586-05
628	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:56.253799-05
630	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:36:58.249158-05
632	church_admin	50	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 50, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:37:00.320074-05
634	system	0	CHURCH_ONBOARDING_COMPLETED	\N	{"resource_type": "church", "resource_id": 50, "church_name": "Grace Community Church", "admin_email": "pastorif30yt@gracechurch.org"}	2025-08-25 14:37:03.363526-05
635	system	0	CHURCH_ONBOARDING_SUBMITTED	\N	{"resource_type": "church", "resource_id": 51, "church_name": "Grace Community Church", "admin_email": "pastortxzjr1@gracechurch.org", "kyc_status": "pending_review", "stripe_account_created": true}	2025-08-25 14:51:16.097747-05
636	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:19.7292-05
637	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:20.245926-05
638	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:21.220884-05
639	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:22.225817-05
640	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:23.201715-05
641	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:24.262493-05
642	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:25.210963-05
643	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:26.237745-05
644	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:27.230974-05
645	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:28.213398-05
646	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:29.258945-05
647	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:30.222466-05
648	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:31.222451-05
649	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:32.223835-05
650	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:33.206884-05
651	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:34.228494-05
652	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:35.233351-05
653	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:36.234025-05
654	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:37.210839-05
655	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:38.237648-05
656	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:39.212024-05
657	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:40.233987-05
658	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:41.237542-05
659	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:42.22611-05
660	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:43.231947-05
661	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:44.21972-05
662	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:45.258966-05
663	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:46.209897-05
664	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:47.228801-05
665	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:48.209877-05
666	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:49.219203-05
667	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:50.219531-05
668	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:51.211262-05
669	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:52.250141-05
670	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:53.222518-05
672	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:55.223966-05
674	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:57.240452-05
676	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:59.24165-05
678	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:01.440154-05
680	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:03.223634-05
682	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:05.209577-05
684	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:07.240806-05
686	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:09.21484-05
688	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:11.209041-05
690	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:13.21883-05
671	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:54.213453-05
673	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:56.224098-05
675	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:51:58.202873-05
677	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:00.246064-05
679	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:02.245877-05
681	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:04.248787-05
683	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:06.311369-05
685	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:08.244098-05
687	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:10.193839-05
689	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:12.224121-05
691	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:14.223836-05
692	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:15.206258-05
693	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:16.224291-05
694	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:17.230577-05
695	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:18.208726-05
696	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:19.209349-05
697	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:20.209226-05
698	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:21.194611-05
699	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:22.200173-05
700	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:23.253939-05
701	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:24.223438-05
702	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:25.201235-05
703	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:26.206529-05
704	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:27.185504-05
705	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:28.239597-05
706	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:29.208626-05
707	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:30.248107-05
708	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:31.2193-05
709	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:32.201588-05
710	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:33.19853-05
711	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:34.218274-05
712	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:35.213243-05
713	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:36.223933-05
714	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:37.224843-05
715	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:38.228495-05
716	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:39.218833-05
717	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:40.299845-05
718	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:41.277819-05
719	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:42.243113-05
720	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:43.219418-05
721	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:44.245561-05
722	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:45.236686-05
724	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:47.213573-05
726	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:49.214868-05
728	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:51.228395-05
730	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:53.218517-05
732	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:55.20439-05
734	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:57.223676-05
736	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:59.219445-05
738	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:01.239514-05
740	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:03.212435-05
742	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:05.223351-05
744	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:07.222256-05
746	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:09.24585-05
748	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:11.213166-05
750	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:13.217856-05
752	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:15.240637-05
754	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:17.354411-05
756	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:19.237911-05
758	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:21.236963-05
760	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:23.210421-05
762	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:25.241311-05
764	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": true, "payouts_enabled": true}	2025-08-25 14:53:27.264332-05
767	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:04.614824-05
769	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:06.155021-05
771	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:08.101801-05
773	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:10.119457-05
775	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:12.104973-05
777	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:14.115268-05
779	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:16.103304-05
781	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:18.167898-05
783	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:20.098561-05
785	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:22.114666-05
787	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:24.143839-05
789	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:26.12216-05
791	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:28.121177-05
793	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:30.101346-05
795	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:32.14576-05
797	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:34.107746-05
799	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:36.113259-05
801	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:38.117319-05
803	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:40.105758-05
723	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:46.216021-05
725	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:48.222083-05
727	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:50.197876-05
729	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:52.213254-05
731	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:54.256681-05
733	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:56.211048-05
735	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:52:58.236969-05
737	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:00.223027-05
739	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:02.215185-05
741	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:04.213672-05
743	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:06.250382-05
745	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:08.206303-05
747	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:10.22799-05
749	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:12.189825-05
751	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:14.226348-05
753	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:16.223765-05
755	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:18.250833-05
757	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:20.22358-05
759	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:22.243871-05
761	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:24.239247-05
763	church_admin	51	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 51, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:53:26.253048-05
765	system	0	CHURCH_ONBOARDING_COMPLETED	\N	{"resource_type": "church", "resource_id": 51, "church_name": "Grace Community Church", "admin_email": "pastortxzjr1@gracechurch.org"}	2025-08-25 14:53:28.77283-05
766	system	0	CHURCH_ONBOARDING_SUBMITTED	\N	{"resource_type": "church", "resource_id": 52, "church_name": "Grace Community Church", "admin_email": "pastorsdybgm@gracechurch.org", "kyc_status": "pending_review", "stripe_account_created": true}	2025-08-25 14:59:02.094493-05
768	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:05.150455-05
770	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:07.122406-05
772	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:09.106586-05
774	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:11.106871-05
776	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:13.128323-05
778	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:15.169266-05
780	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:17.198147-05
782	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:19.107607-05
784	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:21.10627-05
786	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:23.111009-05
788	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:25.110443-05
790	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:27.14684-05
792	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:29.128426-05
794	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:31.110975-05
796	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:33.087791-05
798	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:35.093157-05
800	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:37.135077-05
802	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:39.1062-05
804	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:41.09066-05
806	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:43.101769-05
808	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:45.105638-05
810	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:47.213202-05
812	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:49.125478-05
814	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:51.116542-05
816	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:53.118792-05
818	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:55.120649-05
820	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:57.117396-05
822	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:59.086449-05
824	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:01.304298-05
826	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:03.144311-05
828	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:05.122649-05
830	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:07.271522-05
832	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:09.131526-05
834	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:11.104374-05
836	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:13.090128-05
805	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:42.095248-05
807	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:44.105367-05
809	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:46.106488-05
811	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:48.120316-05
813	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:50.09045-05
815	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:52.119053-05
817	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:54.091537-05
819	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:56.095038-05
821	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 14:59:58.143619-05
823	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:00.113144-05
825	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:02.111738-05
827	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:04.154307-05
829	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:06.120579-05
831	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:08.141396-05
833	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:10.165932-05
835	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:12.140595-05
837	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:14.132762-05
838	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:15.137249-05
839	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:16.108336-05
840	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:17.163702-05
841	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:18.09285-05
842	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:19.131562-05
843	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:20.114711-05
844	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:21.110916-05
845	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:22.134863-05
846	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:23.155103-05
847	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:24.115997-05
848	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:25.133549-05
849	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:26.110427-05
850	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:27.110761-05
851	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:28.107739-05
852	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:29.155092-05
853	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:30.160476-05
854	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:31.09833-05
855	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:32.119228-05
856	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:33.138568-05
857	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:34.15509-05
858	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:35.101617-05
859	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:36.095479-05
860	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:37.1054-05
861	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:38.106583-05
862	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:39.090456-05
864	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:41.105775-05
866	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:43.121086-05
868	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:45.111107-05
870	system	0	CHURCH_ONBOARDING_COMPLETED	\N	{"resource_type": "church", "resource_id": 52, "church_name": "Grace Community Church", "admin_email": "pastorsdybgm@gracechurch.org"}	2025-08-25 15:00:48.375148-05
863	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:40.152424-05
865	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:42.181385-05
867	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": false, "payouts_enabled": false}	2025-08-25 15:00:44.135822-05
869	church_admin	52	STRIPE_ONBOARDING_UPDATED	\N	{"resource_type": "church", "resource_id": 52, "charges_enabled": true, "payouts_enabled": true}	2025-08-25 15:00:46.189886-05
\.


--
-- TOC entry 5374 (class 0 OID 60222)
-- Dependencies: 235
-- Data for Name: bank_accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bank_accounts (id, user_id, account_id, name, mask, subtype, type, institution, access_token, created_at, is_active, updated_at) FROM stdin;
\.


--
-- TOC entry 5376 (class 0 OID 60237)
-- Dependencies: 237
-- Data for Name: beneficial_owners; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.beneficial_owners (id, church_id, first_name, last_name, middle_name, date_of_birth, ssn, email, phone, address_line_1, address_line_2, city, state, zip_code, country, id_type, id_number, id_issuing_country, id_expiration_date, id_front_url, id_back_url, ownership_percentage, title, is_control_person, is_verified, verified_at, verified_by, created_at, updated_at) FROM stdin;
2	26	John	Smith	\N	1980-05-15	123-45-6789	pastor@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 06:18:01.093395-05	\N
3	28	John	Smith	\N	1980-05-15	123-45-6789	pastormii9m3@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 06:49:02.591173-05	\N
4	29	John	Smith	\N	1980-05-15	123-45-6789	pastorlmbr63@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 06:52:49.073136-05	\N
5	30	John	Smith	\N	1980-05-15	123-45-6789	pastor7ib3vg@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:05:12.329769-05	\N
6	31	John	Smith	\N	1980-05-15	123-45-6789	pastorh1zpjq@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:14:41.19409-05	\N
7	32	John	Smith	\N	1980-05-15	123-45-6789	pastorl4aso5@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:16:33.084897-05	\N
8	33	John	Smith	\N	1980-05-15	123-45-6789	pastor81icz8@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:36:32.150637-05	\N
9	34	John	Smith	\N	1980-05-15	123-45-6789	pastorklzct4@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:42:39.709209-05	\N
10	35	John	Smith	\N	1980-05-15	123-45-6789	pastorqsaezl@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:48:00.711015-05	\N
11	36	John	Smith	\N	1980-05-15	123-45-6789	pastor0t0o4o@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:57:51.34359-05	\N
12	37	John	Smith	\N	1980-05-15	123-45-6789	pastorilruey@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 07:58:04.902074-05	\N
13	38	John	Smith	\N	1980-05-15	123-45-6789	pastor5cldg1@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 08:12:29.315256-05	\N
14	39	John	Smith	\N	1980-05-15	123-45-6789	pastorfrkne5@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 08:38:58.139655-05	\N
15	40	John	Smith	\N	1980-05-15	123-45-6789	pastory7s5u0@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 08:51:45.691138-05	\N
16	41	John	Smith	\N	1980-05-15	123-45-6789	pastorh3ma9m@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 10:12:06.909185-05	\N
17	42	John	Smith	\N	1980-05-15	123-45-6789	pastorykdfaz@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 10:46:00.275738-05	\N
18	43	John	Smith	\N	1980-05-15	123-45-6789	pastorwn5kxr@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 10:56:20.2233-05	\N
19	44	John	Smith	\N	1980-05-15	123-45-6789	pastor4ki62l@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 11:05:03.335423-05	\N
20	45	John	Smith	\N	1980-05-15	123-45-6789	pastoruykg8a@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-19 19:05:49.138682-05	\N
21	46	John	Smith	\N	1980-05-15	123-45-6789	pastor9z8lbx@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-22 11:42:13.883381-05	\N
23	48	John	Smith	\N	1980-05-15	123-45-6789	doingcode3333@gmail.com	(555) 123-4567	123 Main Street	\N	Springfield	TX	62701	US	state_id	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-25 13:39:13.123086-05	\N
24	49	John	Smith	\N	1980-05-15	123-45-6789	pastorb2dx9e@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	TX	62701	US	state_id	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-25 13:47:34.959315-05	\N
25	50	John	Smith	\N	1980-05-15	123-45-6789	pastorqm2ldi@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	PA	62701	US	drivers_license	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-25 14:34:42.992237-05	\N
26	51	John	Smith	\N	1980-05-15	123-45-6789	pastor2epweh@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	IL	62701	US	Driver's License	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-25 14:51:11.922659-05	\N
27	52	John	Smith	\N	1980-05-15	123-45-6789	pastor7p8hp4@gracechurch.org	(555) 123-4567	123 Main Street	\N	Springfield	DE	62701	US	state_id	IL123456789	US	\N	\N	\N	100	Senior Pastor / Primary Contact	t	f	\N	\N	2025-08-25 14:58:57.995851-05	\N
\.


--
-- TOC entry 5378 (class 0 OID 60258)
-- Dependencies: 239
-- Data for Name: church_admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.church_admins (id, user_id, church_id, role, is_active, created_at, updated_at, admin_name, permissions, is_primary_admin, can_manage_finances, can_manage_members, can_manage_settings, contact_email, contact_phone, admin_notes, admin_metadata, last_activity, stripe_identity_session_id, identity_verification_status, identity_verification_date) FROM stdin;
49	120	50	admin	t	2025-08-25 14:34:47.15657-05	2025-08-25 14:34:47.156575-05	\N	\N	f	t	t	t	\N	\N	\N	\N	\N	\N	not_started	\N
50	121	51	admin	t	2025-08-25 14:51:15.840815-05	2025-08-25 14:51:15.840819-05	\N	\N	f	t	t	t	\N	\N	\N	\N	\N	\N	not_started	\N
51	122	52	admin	t	2025-08-25 14:59:02.091641-05	2025-08-25 14:59:02.091644-05	\N	\N	f	t	t	t	\N	\N	\N	\N	\N	\N	not_started	\N
\.


--
-- TOC entry 5408 (class 0 OID 69124)
-- Dependencies: 269
-- Data for Name: church_memberships; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.church_memberships (id, user_id, church_id, role, is_active, joined_at, created_at) FROM stdin;
\.


--
-- TOC entry 5362 (class 0 OID 60098)
-- Dependencies: 223
-- Data for Name: church_messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.church_messages (id, church_id, title, content, type, priority, is_active, is_published, created_at, updated_at, published_at) FROM stdin;
1	13	Welcome to Church for frank ting!	Welcome to Church for frank ting! We're excited to have you join our community. Your donations will help support our mission and make a positive impact. Feel free to reach out if you have any questions about our church or how your donations are being used.	GENERAL	MEDIUM	t	t	2025-08-18 13:10:56.86406-05	\N	2025-08-18 13:10:56.872494-05
2	13	Welcome to Church for frank ting!	Welcome to Church for frank ting! We're excited to have you join our community. Your donations will help support our mission and make a positive impact. Feel free to reach out if you have any questions about our church or how your donations are being used.	GENERAL	MEDIUM	t	t	2025-08-18 13:45:48.389114-05	\N	2025-08-18 13:45:48.398666-05
3	13	Welcome to Church for frank ting!	Welcome to Church for frank ting! We're excited to have you join our community. Your donations will help support our mission and make a positive impact. Feel free to reach out if you have any questions about our church or how your donations are being used.	GENERAL	MEDIUM	t	t	2025-08-18 14:21:02.616074-05	\N	2025-08-18 14:21:02.627737-05
4	13	Welcome to Church for frank ting!	Welcome to Church for frank ting! We're excited to have you join our community. Your donations will help support our mission and make a positive impact. Feel free to reach out if you have any questions about our church or how your donations are being used.	GENERAL	MEDIUM	t	t	2025-08-18 14:24:05.38816-05	\N	2025-08-18 14:24:05.40075-05
5	13	Welcome to Church for frank ting!	Welcome to Church for frank ting! We're excited to have you join our community. Your donations will help support our mission and make a positive impact. Feel free to reach out if you have any questions about our church or how your donations are being used.	GENERAL	MEDIUM	t	t	2025-08-18 14:24:35.323207-05	\N	2025-08-18 14:24:35.333614-05
6	13	Welcome to Church for frank ting!	Welcome to Church for frank ting! We're excited to have you join our community. Your donations will help support our mission and make a positive impact. Feel free to reach out if you have any questions about our church or how your donations are being used.	GENERAL	MEDIUM	t	t	2025-08-18 14:37:12.366201-05	\N	2025-08-18 14:37:12.377826-05
\.


--
-- TOC entry 5414 (class 0 OID 69201)
-- Dependencies: 275
-- Data for Name: church_payouts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.church_payouts (id, church_id, stripe_transfer_id, amount_transferred, manna_fees, net_amount, payout_period_start, payout_period_end, donor_count, total_roundups_processed, status, created_at, transferred_at) FROM stdin;
\.


--
-- TOC entry 5364 (class 0 OID 60114)
-- Dependencies: 225
-- Data for Name: church_referrals; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.church_referrals (id, referring_church_id, referred_church_id, referral_code, payout_status, payout_amount, payout_date, stripe_transfer_id, created_at, updated_at, commission_rate, total_commission_earned, commission_paid, commission_period_months, activated_at, expires_at) FROM stdin;
\.


--
-- TOC entry 5360 (class 0 OID 60043)
-- Dependencies: 221
-- Data for Name: churches; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.churches (id, name, ein, website, phone, address, email, kyc_status, kyc_submitted_at, kyc_approved_at, kyc_approved_by, kyc_rejected_at, kyc_rejected_by, kyc_rejection_reason, kyc_data, articles_of_incorporation_url, irs_letter_url, bank_statement_url, board_resolution_url, documents, tax_exempt, anti_terrorism, legitimate_entity, consent_checks, ownership_disclosed, info_accurate, referral_code, is_active, status, stripe_account_id, created_at, updated_at, city, state, zip_code, tax_id, pastor_name, pastor_email, pastor_phone, kyc_state, charges_enabled, payouts_enabled, disabled_reason, requirements_json, verified_at, document_status, document_notes, document_requests, legal_name, address_line_1, address_line_2, country, kyc_additional_data, primary_purpose, total_received) FROM stdin;
33	Grace Community Church	12-q916dtn	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor48inye@gracechurch.org	pending_review	2025-08-19 07:36:32.15958-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-q916dtn", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor81icz8@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxomHRcNjkgcXgT	2025-08-19 07:36:32.161862-05	2025-08-19 07:38:20.0386-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
52	Grace Community Church	12-yli2l90	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorsdybgm@gracechurch.org	pending_review	2025-08-25 14:58:57.997102-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-yli2l90", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor7p8hp4@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "DE", "postal_code": "62701"}, "gov_id": {"type": "state_id", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": true, "sanctions_compliance": true, "no_fictitious_entity": true, "background_check_consent": true, "beneficial_ownership": true, "accuracy_certification": true}}	\N	\N	\N	\N	\N	t	t	t	t	t	t	\N	t	active	acct_1S06XgDyKtLVlpWo	2025-08-25 14:58:57.997741-05	2025-08-25 15:00:46.188199-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
45	Grace Community Church	12-yvi7kyf	https://gracechurch.org	(555) 123-4567	123 Main Street	pastormqe12s@gracechurch.org	pending_review	2025-08-19 19:05:49.283074-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-yvi7kyf", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastoruykg8a@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxzXHDMlxJHenSH	2025-08-19 19:05:49.286238-05	2025-08-19 19:07:31.440126-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
34	Grace Community Church	12-8d5r0au	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor0lkt7b@gracechurch.org	pending_review	2025-08-19 07:42:39.716958-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-8d5r0au", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorklzct4@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": true, "sanctions_compliance": true, "no_fictitious_entity": true, "background_check_consent": true, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	t	t	t	t	f	f	\N	t	active	acct_1RxosCRZc9FOT6MK	2025-08-19 07:42:39.718792-05	2025-08-19 07:44:27.964447-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["individual.dob.day", "individual.dob.month", "individual.dob.year", "individual.ssn_last_4"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
46	Grace Community Church	12-5vxotno	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorftzr7b@gracechurch.org	pending_review	2025-08-22 11:42:13.885028-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-5vxotno", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor9z8lbx@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1Ryy2fRgZM8AzMIa	2025-08-22 11:42:13.886537-05	2025-08-22 11:44:43.098567-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
35	Grace Community Church	12-gtufyqj	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorgtbyex@gracechurch.org	pending_review	2025-08-19 07:48:00.719359-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-gtufyqj", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorqsaezl@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1RxoxNDH0Aqw6epj	2025-08-19 07:48:00.721241-05	2025-08-19 07:48:06.385624-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	{"alternatives": [], "current_deadline": null, "currently_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "disabled_reason": "requirements.past_due", "errors": [], "eventually_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "past_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
36	Grace Community Church	12-9t2knay	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor16vst4@gracechurch.org	pending_review	2025-08-19 07:57:51.352187-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-9t2knay", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor0t0o4o@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1Rxp6uDQOAnM2BA3	2025-08-19 07:57:51.35465-05	2025-08-19 07:57:56.186841-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	\N	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
37	Grace Community Church	12-vt4fjam	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor5sptt9@gracechurch.org	pending_review	2025-08-19 07:58:04.910075-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-vt4fjam", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorilruey@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1Rxp77RjkgKLUxIN	2025-08-19 07:58:04.911722-05	2025-08-19 07:59:35.150635-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
38	Grace Community Church	12-lpzr2va	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorb8v8t3@gracechurch.org	pending_review	2025-08-19 08:12:29.31711-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-lpzr2va", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor5cldg1@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxpL3DEpijAN9Oy	2025-08-19 08:12:29.317761-05	2025-08-19 08:38:53.655026-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
47	Test Community Church	12-plg3gvb	https://gracechurch.org	(555) 123-4567	123 Main Street	benjaminvancauwenbergh86215@gmail.com	pending_review	2025-08-22 12:29:55.285999-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-plg3gvb", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "benjaminvancauwenbergh86215@gmail.com", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RyymqDpUdeo2XNe	2025-08-22 12:29:55.288181-05	2025-08-24 16:16:15.561712-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
51	Grace Community Church	12-wlem42c	https://gracechurch.org	(555) 123-4567	123 Main Street	pastortxzjr1@gracechurch.org	pending_review	2025-08-25 14:51:11.924767-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-wlem42c", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor2epweh@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1S06QADD0LApF1vx	2025-08-25 14:51:11.925553-05	2025-08-25 14:53:27.262434-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
39	Grace Community Church	12-4d9k3qs	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorc5f9kn@gracechurch.org	pending_review	2025-08-19 08:38:58.140696-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-4d9k3qs", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorfrkne5@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxpkfDqmLimDV5j	2025-08-19 08:38:58.141129-05	2025-08-19 08:41:59.596983-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
40	Grace Community Church	12-npd4ur0	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor6ylg1k@gracechurch.org	pending_review	2025-08-19 08:51:45.692784-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-npd4ur0", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastory7s5u0@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1Rxpx7RgIFPSxdaA	2025-08-19 08:51:45.693358-05	2025-08-19 10:11:03.537297-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	{"alternatives": [], "current_deadline": null, "currently_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "disabled_reason": "requirements.past_due", "errors": [], "eventually_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "past_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
48	Grace Community Church	12-pij8udy	https://gracechurch.org	(555) 123-4567	123 Main Street	doingcode333@gmail.com	pending_review	2025-08-25 13:39:13.135844-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-pij8udy", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "doingcode3333@gmail.com", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "TX", "postal_code": "62701"}, "gov_id": {"type": "state_id", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": true, "sanctions_compliance": true, "no_fictitious_entity": true, "background_check_consent": true, "beneficial_ownership": true, "accuracy_certification": true}}	\N	\N	\N	\N	\N	t	t	t	t	t	t	\N	t	active	acct_1S05IVRXEs4OAV3Y	2025-08-25 13:39:13.141254-05	2025-08-25 13:41:23.234897-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
50	Grace Community Church	12-4coedxe	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorif30yt@gracechurch.org	pending_review	2025-08-25 14:34:42.993957-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-4coedxe", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorqm2ldi@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "PA", "postal_code": "62701"}, "gov_id": {"type": "drivers_license", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": true, "sanctions_compliance": true, "no_fictitious_entity": true, "background_check_consent": true, "beneficial_ownership": true, "accuracy_certification": true}}	\N	\N	\N	\N	\N	t	t	t	t	t	t	\N	t	active	acct_1S06ADDvOfQEgnaj	2025-08-25 14:34:42.995249-05	2025-08-25 14:37:01.319576-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
13	Church for frank ting	32423423414342	https://church.manna.com	21324323432		churchadmin@manna.com	approved	2025-08-14 23:05:50.681242-05	2025-08-14 23:11:01.590587-05	3	\N	\N	\N	\N	/uploads/church_docs/20250815_000604_2c3b196b.pdf	/uploads/church_docs/20250815_000614_5b32a3a8.pdf	/uploads/church_docs/20250815_000629_a0add7ed.pdf	/uploads/church_docs/20250815_000654_e109b761.pdf	{"irs_letter": {"status": "rejected", "rejected_at": "2025-08-16T02:22:47.553061+00:00", "rejected_by": 1, "rejection_reason": "sdafsdfdsa", "uploaded": false}}	t	t	t	f	f	f	\N	t	active	\N	2025-08-14 22:57:17.646159-05	2025-08-15 23:08:36.119101-05	Ghent	TX	12345	\N	\N	\N	\N	ACTIVE	f	f	\N	\N	2025-08-14 23:11:01.590618-05	"{\\"articles_of_incorporation\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-16T03:01:26.405596+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"sdafsfsdaf\\"}, \\"irs_letter\\": {\\"status\\": \\"rejected\\", \\"rejected_at\\": \\"2025-08-16T03:32:18.888947+00:00\\", \\"rejected_by\\": 3, \\"rejection_reason\\": \\"xcxzfdsfaasd\\", \\"rejected\\": true}, \\"bank_statement\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-15T04:08:02.114526+00:00\\", \\"approved_by\\": 3, \\"notes\\": null}, \\"board_resolution\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-15T04:08:03.213503+00:00\\", \\"approved_by\\": 3, \\"notes\\": null}, \\"tax_exempt_letter\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-15T13:35:49.275361+00:00\\", \\"approved_by\\": 3, \\"notes\\": \\"Document approved after review\\"}}"	{"tax_exempt_letter": {"notes": "This document looks good, but needs additional verification", "updated_at": "2025-08-15T13:35:49.260396+00:00", "updated_by": 3}, "articles_of_incorporation": {"notes": "sdfafsdaf", "updated_at": "2025-08-16T00:45:34.543465+00:00", "updated_by": 1}}	\N	churchadmin	street address	sadfsafsdfsdafsdafsdafsdafsdafsd	US	"{\\"articles_metadata\\": {\\"file_info\\": {\\"filename\\": \\"Algomasterio_System_Design_Interview_Handbook.pdf\\", \\"content_type\\": \\"application/pdf\\", \\"size\\": 2579995, \\"document_type\\": \\"articles_of_incorporation\\", \\"uploaded_at\\": \\"2025-08-15T04:06:04.647872+00:00\\", \\"file_hash\\": \\"5e1a7f87312e393c84d97cebb7d85579492d0bf65e3a1ea6edf706b468fb8352\\", \\"metadata\\": {\\"document_type\\": \\"articles_of_incorporation\\", \\"processing_timestamp\\": \\"2025-08-15T04:06:03.337844+00:00\\", \\"file_hash\\": \\"5e1a7f87312e393c84d97cebb7d85579492d0bf65e3a1ea6edf706b468fb8352\\", \\"extracted_text\\": \\"SYSTEM  D ESIG N \\\\n75 pages guide to ace your next\\\\nSystem Design InterviewASH ISH  PRATAP SING H\\\\nAlgoMaster.ioINTERVIEW  H AND BO O K\\\\nTable of Contents\\\\nFundamentals\\\\n1. Scalability\\\\n2. Availability\\\\n3. Latency vs Throughput\\\\n4. CAP Theorem\\\\n5. Load Balancers\\\\n6. Databases\\\\n7. CDN\\\\n8. Message Queues\\\\n9. Rate Limiting\\\\n10. Database Indexes\\\\n11. Caching\\\\n12. Consistent Hashing\\\\n13. Database Sharding\\\\n14. Consensus Algorithms6\\\\n7\\\\n8\\\\n9\\\\n10\\\\n11\\\\n12\\\\n13\\\\n14\\\\n15\\\\n16\\\\n18\\\\n19\\\\n20\\\\n15. Proxy Servers\\\\n16. Heartbeats\\\\n17. Checksums\\\\n18. Service Discovery\\\\n19. Bloom Filters\\\\n20. Gossip Protocol21\\\\n22\\\\n23\\\\n24\\\\n25\\\\n26\\\\nTrade-offs\\\\n1. Vertical vs Horizontal Scaling\\\\n2. Strong vs Eventual Consistency28\\\\n29\\\\n30\\\\n31\\\\n33\\\\n353. Stateful vs Stateless Design\\\\n4. Read vs Write Through Cache\\\\n5. SQL vs NoSQL\\\\n6. REST vs RPC\\\\n37\\\\n38\\\\n39\\\\n41\\\\n437. Synchronous vs Asynchronous\\\\n8. Batch vs Stream Processing\\\\n9. Long Polling vs WebSockets\\\\n10. Normalization vs Denormalization\\\\n11. TCP vs UDP\\\\nSystem Design Interview Template\\\\n40 System Design Interview TipsArchitectural Patterns\\\\n45\\\\n46\\\\n47\\\\n48\\\\n491. Client-Server Architecture\\\\n2. Microservices Architecture\\\\n3. Serverless Architecture\\\\n4. Event-Driven Architecture\\\\n5. Peer-to-Peer Architecture\\\\n10 most common Interview Questions 656050\\\\n SYSTEM DESIGN \\\\nFUNDAMENTALS\\\\nAs a system grows, the performance starts to \\\\ndegrade unless we adapt it to deal with that growth.\\\\nScalability is the property of a system to handle a \\\\ngrowing amount of load by adding resources to the \\\\nsystem.\\\\nA system that can continuously evolve to support a \\\\ngrowing amount of work is scalable.\\\\n1. Scalability\\\\n2. Availability\\\\nAvailability refers to the proportion of time a system \\\\nis operational and accessible when required.\\\\nAvailability = Uptime / (Uptime + Downtime)\\\\nUptime: The period during which a system is\\\\nfunctional and accessible.\\\\nDowntime: The period during which a system is\\\\nunavailable due to failures, maintenance, or other\\\\nissues.\\\\nAvailability Tiers:\\\\n\\\\n3. Latency vs Throughput\\\\nLatency\\\\nLatency refers to the time it takes for a single \\\\noperation or request to complete.\\\\nLow latency means faster response times and a\\\\nmore responsive system.\\\\nHigh latency can lead to lag and poor user\\\\nexperience.\\\\nThroughput\\\\nThroughput measures the amount of work done or \\\\ndata processed in a given period of time.\\\\nIt is typically expressed in terms of requests per \\\\nsecond (RPS) or transactions per second (TPS).\\\\n4. CAP Theorem\\\\nCAP stands for Consistency, Availability, and \\\\nPartition Tolerance, and the theorem states that:\\\\nIt is impossible for a distributed data store to\\\\nsimultaneously provide all three guarantees.\\\\nConsistency (C): Every read receives the most\\\\nrecent write or an error.\\\\nAvailability (A): Every request (read or write)\\\\nreceives a non-error response, without guarantee\\\\nthat it contains the most recent write.\\\\nPartition Tolerance (P): The system continues to\\\\noperate despite an arbitrary number of messages\\\\nbeing dropped (or delayed) by the network\\\\nbetween nodes.\\\\n5. Load Balancers\\\\nLoad Balancers distribute incoming network traffic\\\\nacross multiple servers to ensure that no single\\\\nserver is overwhelmed.\\\\nPopular Load Balancing Algorithms:\\\\nRound Robin: Distributes requests evenly in\\\\ncircular order.1.\\\\nWeighted Round Robin: Distributes requests\\\\nbased on server capacity weights.2.\\\\nLeast Connections: Sends requests to server with\\\\nfewest active connections.3.\\\\nLeast Response Time: Routes requests to server\\\\nwith fastest response.4.\\\\nIP Hash: Assigns requests based on hashed client\\\\nIP address.5.\\\\n\\\\n6. Databases\\\\nA database is an organized collection of structured\\\\nor unstructured data that can be easily accessed,\\\\nmanaged, and updated.\\\\nTypes of Databases\\\\n1. Relational Databases (RDBMS)\\\\n2. NoSQL Databases\\\\n3. In-Memory Databases\\\\n4. Graph Databases\\\\n5. Time Series Databases\\\\n6. Spatial Databases\\\\nA CDN is a geographically distributed network of\\\\nservers that work together to deliver web content\\\\n(like HTML pages, JavaScript files, stylesheets,\\\\nimages, and videos) to users based on their\\\\ngeographic location.\\\\nThe primary purpose of a CDN is to deliver content\\\\nto end-users with high availability and performance\\\\nby reducing the physical distance between the\\\\nserver and the user.\\\\nWhen a user requests content from a website, the\\\\nCDN redirects the request to the nearest server in its\\\\nnetwork, reducing latency and improving load times.\\\\n7. Content Delivery\\\\nNetwork (CDN)\\\\n8. Message Queues\\\\nA message queue is a communication mechanism\\\\nthat enables different parts of a system to send and\\\\nreceive messages asynchronously.\\\\nProducers can send messages to the queue and\\\\nmove on to other tasks without waiting for\\\\nconsumers to process the messages.\\\\nMultiple consumers can pull messages from the\\\\nqueue, allowing work to be distributed and balanced\\\\nacross different consumers.\\\\n\\\\n9. Rate Limiting\\\\nRate limiting helps protects services from being\\\\noverwhelmed by too many requests from a single\\\\nuser or client.\\\\nRate Limiting Algorithms:\\\\nToken Bucket: Allows bursts traffic within overall\\\\nrate limit.1.\\\\nLeaky Bucket: Smooths traffic flow at constant\\\\nrate.2.\\\\nFixed Window Counter: Limits requests in fixed\\\\ntime intervals.3.\\\\nSliding Window Log: Tracks requests within\\\\nrolling time window.4.\\\\nSliding Window Counter: Smooths rate between\\\\nadjacent fixed windows.5.\\\\n\\\\n10. Database Indexes\\\\nA database index is a super-efficient lookup table\\\\nthat allows a database to find data much faster.\\\\nIt holds the indexed column values along with\\\\npointers to the corresponding rows in the table.\\\\nWithout an index, the database might have to scan\\\\nevery single row in a massive table to find what you\\\\nwant \\\\u2013 a painfully slow process.\\\\nBut, with an index, the database can zero in on the\\\\nexact location of the desired data using the index\\\\u2019s\\\\npointers.\\\\nCaching is a technique used to temporarily store\\\\ncopies of data in high-speed storage layers to reduce\\\\nthe time taken to access data.\\\\nThe primary goal of caching is to improve system\\\\nperformance by reducing latency, offloading the\\\\nmain data store, and providing faster data retrieval.\\\\nCaching Strategies:\\\\nRead-Through Cache: Automatically fetches and\\\\ncaches missing data from source.1.\\\\nWrite-Through Cache: Writes data to cache and\\\\nsource simultaneously.2.\\\\nWrite-Back Cache: Writes to cache first, updates\\\\nsource later.3.\\\\nCache-Aside: Application manages data retrieval\\\\nand cache population.4.\\\\n11. Caching\\\\n\\\\nCaching Eviction Policies:\\\\nLeast Recently Used (LRU): Removes the item\\\\nthat hasn't been accessed for the longest time.1.\\\\nLeast Frequently Used (LFU): Discards items with\\\\nthe lowest access frequency over time.2.\\\\nFirst In, First Out (FIFO): Removes the oldest\\\\nitem, regardless of its usage frequency.3.\\\\nTime-to-Live (TTL): Automatically removes items\\\\nafter a predefined expiration time has passed.4.\\\\nConsistent Hashing is a special kind of hashing\\\\ntechnique that allows for efficient distribution of\\\\ndata across a cluster of nodes.\\\\nConsistent hashing ensures that only a small portion\\\\nof the data needs to be reassigned when nodes are\\\\nadded or removed.\\\\n12. Consistent Hashing\\\\nHow Does it Work?\\\\nHash Space: Imagine a fixed circular space or \\\\\\"ring\\\\\\"\\\\nranging from 0 to 2^n-1.1.\\\\nMapping Servers: Each server is mapped to one or\\\\nmore points on this ring using a hash function.2.\\\\nMapping Data: Each data item is also hashed onto\\\\nthe ring.3.\\\\nData Assignment: A data item is stored on the first\\\\nserver encountered while moving clockwise on the\\\\nring from the item's position.4.\\\\n\\\\n13. Database Sharding\\\\nDatabase sharding is a horizontal scaling technique\\\\nused to split a large database into smaller,\\\\nindependent pieces called shards.\\\\nThese shards are then distributed across multiple\\\\nservers or nodes, each responsible for handling a\\\\nspecific subset of the data.\\\\nBy distributing the data across multiple nodes,\\\\nsharding can significantly reduce the load on any\\\\nsingle server, resulting in faster query execution and\\\\nimproved overall system performance.\\\\n\\\\nIn a distributed system, nodes need to work together\\\\nto maintain a consistent state. \\\\nHowever, due to the inherent challenges like network\\\\nlatency, node failures, and asynchrony, achieving\\\\nthis consistency is not straightforward. \\\\nConsensus algorithms address these challenges by\\\\nensuring that all participating nodes agree on the\\\\nsame state or sequence of events, even when some\\\\nnodes might fail or act maliciously.\\\\n14. Consensus Algorithms\\\\nPopular Consensus Algorithms\\\\n1. Paxos: Paxos works by electing a leader that\\\\nproposes a value, which is then accepted by a\\\\nmajority of the nodes.\\\\n2. Raft: Raft works by designating one node as the\\\\nleader to manage log replication and ensure\\\\nconsistency across the cluster.\\\\n\\\\n15. Proxy Servers\\\\nA proxy server acts as a gateway between you and\\\\nthe internet. It's an intermediary server separating\\\\nend users from the websites they browse.\\\\n2 Common types of Proxy Servers:\\\\nForward Proxies: Sits in front of a client and\\\\nforwards requests to the internet on behalf of the\\\\nclient.1.\\\\nReverse Proxies: Sits in front of a web server and\\\\nforwards requests from clients to the server.2.\\\\n\\\\n16. HeartBeats\\\\nIn distributed systems, a heartbeat is a periodic\\\\nmessage sent from one component to another to\\\\nmonitor each other's health and status.\\\\nWithout a heartbeat mechanism, it's hard to quickly\\\\ndetect failures in a distributed system, leading to:\\\\nDelayed fault detection and recovery\\\\nIncreased downtime and errors\\\\nDecreased overall system reliability\\\\n17. Checksums\\\\nA checksum is a unique fingerprint attached to the\\\\ndata before it's transmitted. \\\\nWhen the data arrives at the recipient's end, the\\\\nfingerprint is recalculated to ensure it matches the\\\\noriginal one.\\\\nIf the checksum of a piece of data matches the\\\\nexpected value, you can be confident that the data\\\\nhasn't been modified or damaged.\\\\n\\\\n18. Service Discovery\\\\nService discovery is a mechanism that allows services\\\\nin a distributed system to find and communicate with\\\\neach other dynamically. \\\\nIt hides the complex details of where services are\\\\nlocated, so they can interact without knowing each\\\\nother's exact network spots.\\\\nService discovery registers and maintains a record of\\\\nall your services in a service registry. \\\\nThis service registry acts as a single source of truth\\\\nthat allows your services to query and communicate\\\\nwith each other.\\\\n\\\\nA Bloom filter is a probabilistic data structure that\\\\nis primarily used to determine whether an element\\\\nis definitely not in a set or possibly in the set.\\\\nHow Does It Work?\\\\nSetup: Start with a bit array of m bits, all set to\\\\n0, and k different hash functions.1.\\\\nAdding an element: To add an element, feed it\\\\nto each of the k hash functions to get k array\\\\npositions. Set the bits at all these positions to 1.2.\\\\nQuerying: To query for an element, feed it to\\\\neach of the k hash functions to get k array\\\\npositions. If any of the bits at these positions\\\\nare 0, the element is definitely not in the set. If\\\\nall are 1, then either the element is in the set, or\\\\nwe have a false positive.3.\\\\n19. Bloom Filters\\\\nGossip Protocol is a decentralized communication\\\\nprotocol used in distributed systems to spread\\\\ninformation across all nodes.\\\\nIt is inspired by the way humans share news by word-\\\\nof-mouth, where each person who learns the\\\\ninformation shares it with others, leading to\\\\nwidespread dissemination.\\\\n20. Gossip Protocol\\\\nHow does it work?\\\\nInitialization: A node in the system starts with a\\\\npiece of information, known as a \\\\\\"gossip.\\\\\\"1.\\\\nGossip Exchange: At regular intervals, each node\\\\nrandomly selects another node and shares its\\\\ncurrent gossip. The receiving node then merges\\\\nthe received gossip with its own.2.\\\\nPropagation: The process repeats, with each node\\\\nspreading the gossip to others.3.\\\\nConvergence: Eventually, every node in the\\\\nnetwork will have received the gossip, ensuring\\\\nthat all nodes have consistent information.4.\\\\n\\\\nSYSTEM DESIGN\\\\nTRADE-OFFS\\\\n1. Vertical vs Horizontal Scaling\\\\nVertical scaling involves boosting the power of an\\\\nexisting machine (eg.. CPU, RAM, Storage) to handle\\\\nincreased loads.\\\\nScaling vertically is simpler but there's a physical\\\\nlimit to how much you can upgrade a single machine\\\\nand it introduces a single point of failure.\\\\nHorizontal scaling involves adding more servers or\\\\nnodes to the system to distribute the load across\\\\nmultiple machines.\\\\nScaling horizontally allows for almost limitless\\\\nscaling but brings complexity of managing\\\\ndistributed systems.\\\\n\\\\n2. Strong vs Eventual Consistency\\\\nStrong consistency ensures that any read operation\\\\nreturns the most recent write for a given piece of\\\\ndata.\\\\nThis means that once a write is acknowledged, all\\\\nsubsequent reads will reflect that write\\\\nEventual consistency ensures that, given enough\\\\ntime, all nodes in the system will converge to the\\\\nsame value. \\\\nHowever, there are no guarantees about when this\\\\nconvergence will occur.\\\\n3. Stateful vs Stateless Design\\\\nIn a stateful design, the system remembers client\\\\ndata from one request to the next.\\\\nIt maintains a record of the client's state, which can\\\\ninclude session information, transaction details, or\\\\nany other data relevant to the ongoing interaction.\\\\nStateless design treats each request as an\\\\nindependent transaction. The server does not store\\\\nany information about the client's state between\\\\nrequests.\\\\nEach request must contain all the information\\\\nnecessary to understand and process it.\\\\n\\\\n4. Read-Through vs  Write-Through\\\\nCache\\\\n\\\\nA Read-Through cache sits between your application\\\\nand your data store.\\\\nWhen your application requests data, it first checks\\\\nthe cache.\\\\nIf the data is found in the cache (a cache hit), it's\\\\nreturned to the application.\\\\nIf the data is not in the cache (a cache miss), the\\\\ncache itself is responsible for loading the data from\\\\nthe data store, caching it, and then returning it to the\\\\napplication.\\\\nIn a Write-Through cache strategy, data is written\\\\ninto the cache and the corresponding database\\\\nsimultaneously.\\\\nEvery write operation writes data to both the cache\\\\nand the data store.\\\\nThe write operation is only considered complete\\\\nwhen both writes are successful.\\\\n5. SQL vs NoSQL\\\\nSQL databases use structured query language and\\\\nhave a predefined schema. They're ideal for:\\\\nComplex queries: SQL is powerful for querying\\\\ncomplex relationships between data.\\\\nACID compliance: Ensures data validity in high-\\\\nstake transactions (e.g., financial systems).\\\\nStructured data: When your data structure is\\\\nunlikely to change.\\\\nExamples: MySQL, PostgreSQL, Oracle\\\\nNoSQL databases are more flexible and scalable.\\\\nThey're best for:\\\\nBig Data: Can handle large volumes of structured\\\\nand unstructured data.\\\\nRapid development: Schema-less nature allows\\\\nfor quicker iterations.\\\\nScalability: Easier to scale horizontally.\\\\nExamples: MongoDB, Cassandra, Redis\\\\n6. REST vs  RPC\\\\nWhen designing APIs, two popular architectural\\\\nstyles often come into consideration: REST\\\\n(Representational State Transfer) and RPC (Remote\\\\nProcedure Call). Both have their strengths and ideal\\\\nuse cases. Let's dive into their key differences to help\\\\nyou choose the right one for your project.\\\\nREST (Representational State Transfer)\\\\nREST is an architectural style that uses HTTP\\\\nmethods to interact with resources.\\\\nKey characteristics:\\\\nStateless: Each request contains all necessary\\\\ninformation\\\\nResource-based: Uses URLs to represent\\\\nresources\\\\nUses standard HTTP methods (GET, POST, PUT,\\\\nDELETE)\\\\nTypically returns data in JSON or XML format\\\\nRPC (Remote Procedure Call)\\\\nRPC is a protocol that one program can use to\\\\nrequest a service from a program located on another\\\\ncomputer in a network.\\\\nKey characteristics:\\\\nAction-based: Focuses on operations or actions\\\\nCan use various protocols (HTTP, TCP, etc.)\\\\nOften uses custom methods\\\\nTypically returns custom data formats\\\\n7. Synchronous vs  Asynchronous\\\\n\\\\ud83d\\\\udd39 Synchronous Processing:\\\\nTasks are executed sequentially.\\\\nMakes it easier to reason about code and handle\\\\ndependencies.\\\\nUsed in scenarios where tasks must be completed\\\\nin order like reading a file line by line.\\\\n\\\\ud83d\\\\udd39 Asynchronous Processing:\\\\nTasks are executed concurrently.\\\\nImproves responsiveness and performance,\\\\nespecially in I/O-bound operations\\\\nUsed when you need to handle multiple tasks\\\\nsimultaneously without blocking the main thread.\\\\nlike background processing jobs.\\\\n8. Batch vs  Stream Processing\\\\n\\\\ud83d\\\\udd39 Batch Processing:\\\\nProcess large volumes of data at once, typically at\\\\nscheduled intervals.\\\\nEfficient for handling massive datasets, ideal for\\\\ntasks like reporting or data warehousing.\\\\nHigh Latency -  results are available only after the\\\\nentire batch is processed.\\\\nExamples: ETL jobs, data aggregation, periodic\\\\nbackups.\\\\n\\\\ud83d\\\\udd39 Stream Processing:\\\\nProcess data in real-time as it arrives.\\\\nPerfect for real-time analytics, monitoring, and\\\\nalerting systems.\\\\nMinimal latency since data is processed within\\\\nmilliseconds or seconds of arrival.\\\\nExamples: Real-time fraud detection, live data\\\\nfeeds, IoT applications.\\\\n9. Long Polling vs WebSockets\\\\n\\\\nWebsokcet establishes a persistent, full-duplex\\\\nconnection between the client and server,\\\\nallowing real-time data exchange without the\\\\noverhead of HTTP requests.\\\\nUnlike the traditional HTTP protocol, where the\\\\nclient sends a request to the server and waits for\\\\na response, WebSockets allow both the client\\\\nand server to send messages to each other\\\\nindependently and continuously after the\\\\nconnection is established.In a Long Polling connection, the client repeatedly\\\\nrequests updates from the server at regular\\\\nintervals. \\\\nIf the server has new data, it sends a response\\\\nimmediately; otherwise, it holds the connection until\\\\ndata is available. \\\\nThis can lead to Increased latency and higher server\\\\nload due to frequent requests, even when no data is\\\\navailable.\\\\n10. Normalization vs Denormalization\\\\nNormalization in database design involves splitting\\\\nup data into related tables to ensure each piece of\\\\ninformation is stored only once.\\\\nIt aims to reduce redundancy and improve data\\\\nintegrity.\\\\nExample: A customer database can have two\\\\nseparate tables: one for customer details and\\\\nanother for orders, avoiding duplication of customer\\\\ninformation for each order.\\\\nDenormalization is the process of combining data\\\\nback into fewer tables to improve query\\\\nperformance. \\\\nThis often means introducing redundancy (duplicate\\\\ninformation) back into your database.\\\\nExample: A blog website can store the latest\\\\ncomments with the posts in the same table\\\\n(denormalized) to speed up the display of post and\\\\ncomments, instead of storing them separately\\\\n(normalized).\\\\n11. TCP vs UDP\\\\nWhen it comes to data transmission over the\\\\ninternet, two key protocols are at the forefront: TCP\\\\nand UDP. \\\\n\\\\ud83d\\\\udd39 TCP (Transmission Control Protocol):\\\\nReliable: Ensures all data packets arrive in order\\\\nand are error-free.\\\\nConnection-Oriented: Establishes a connection\\\\nbefore data transfer, making it ideal for tasks\\\\nwhere accuracy is crucial (e.g., web browsing, file\\\\ntransfers).\\\\nSlower: The overhead of managing connections\\\\nand ensuring reliability can introduce latency.\\\\n\\\\ud83d\\\\udd39 UDP (User Datagram Protocol):\\\\nFaster: Minimal overhead allows for quick data\\\\ntransfer, perfect for time-sensitive applications.\\\\nConnectionless: No formal connection setup;\\\\ndata is sent without guarantees, making it ideal\\\\nfor real-time applications (e.g., video streaming,\\\\nonline gaming).\\\\nUnreliable: No error-checking or ordering, so\\\\nsome data packets might be lost or arrive out of\\\\norder.\\\\nARCHITECTURAL\\\\nPATTERNS\\\\nIn this model, the system is divided into two main\\\\ncomponents: the client and the server.\\\\nClient: The client is typically the user-facing part\\\\nof the system, such as a web browser, mobile\\\\napp, or desktop application. Clients send\\\\nrequests to the server and display the results to\\\\nthe user.\\\\nServer: The server processes client requests,\\\\nmanages resources like databases, and sends the\\\\nrequired data or services back to the client.\\\\n1. Client-Server Architecture\\\\n\\\\n2. Microservices Architecture\\\\nMicroservices architecture is an approach to\\\\ndesigning a system as a collection of loosely\\\\ncoupled, independently deployable services. \\\\nEach microservice corresponds to a specific\\\\nbusiness function and communicates with other\\\\nservices via lightweight protocols, often HTTP/REST\\\\nor messaging queues.\\\\nServices are small, focused on doing one thing well\\\\nand each service has its own database to ensure\\\\nloose coupling.\\\\n3. Serverless Architecture\\\\nServerless architecture abstracts away the\\\\nunderlying infrastructure, allowing developers to\\\\nfocus solely on writing code. \\\\nIn a serverless model, the cloud provider\\\\nautomatically manages the infrastructure, scaling,\\\\nand server maintenance. \\\\nDevelopers deploy functions that are triggered by\\\\nevents, and they are billed only for the compute time\\\\nconsumed.\\\\nIdeal for applications that react to events, such as\\\\nprocessing files, triggering workflows, or handling\\\\nreal-time data streams.\\\\n4. Event-Driven Architecture\\\\nEvent-Driven Architecture (EDA) is a design pattern\\\\nin which the system responds to events, or changes\\\\nin state, that are propagated throughout the system. \\\\nIn EDA, components are decoupled and\\\\ncommunicate through events, which are typically\\\\nhandled asynchronously. \\\\nEvents can be processed in parallel by multiple\\\\nconsumers, allowing the system to scale efficiently.\\\\n\\\\n5. Peer-to-Peer (P2P) Architecture\\\\nP2P architecture is a decentralized model where\\\\neach node, or \\\\\\"peer,\\\\\\" in the network has equal\\\\nresponsibilities and capabilities.\\\\nUnlike the client-server model, there is no central\\\\nserver; instead, each peer can act as both a client\\\\nand a server, sharing resources and data directly\\\\nwith other peers. \\\\nP2P networks are known for their resilience and\\\\nscalability since there is no central point of failure\\\\nand system can scale easily as new peers join the\\\\nnetwork.\\\\n\\\\nSYSTEM DESIGN\\\\nINTERVIEW\\\\nTEMPLATE\\\\nA step-by-step guide to \\\\nSystem Design Interviews\\\\nStep 1. Clarify Requirements\\\\nFunctional Requirements:\\\\nWhat are the core features that the system\\\\nshould support?\\\\nWho are the users (eg.. customers, internal teams\\\\netc.)?\\\\nHow will users interact with the system (eg.. web,\\\\nmobile app, API, etc.)?\\\\nWhat are the key data types the system must\\\\nhandle (text, images, structured data, etc). \\\\nAre there any external systems or third-party\\\\nservices the system needs to integrate with?\\\\nNon-Functional Requirements:\\\\nIs the system read heavy or write heavy and\\\\nwhat\\\\u2019s the read-to-write ratio?\\\\nCan the system have some downtime, or does it\\\\nneed to be highly available?\\\\nAre there any specific latency requirements?\\\\nHow critical is data consistency?\\\\nShould we rate limit the users to prevent abuse of\\\\nthe system?Start by clarifying functional and non-functional\\\\nrequirements. Here are things to consider:\\\\nStep 2. Capacity Estimation\\\\nEstimate capacity to get an overall idea about how\\\\nbig a system you are going to design.\\\\nThis can include things like:\\\\nHow many users are expected to use the system\\\\ndaily and monthly and maximum concurrent\\\\nusers during peak hours?\\\\nExpected read/write requests per second.\\\\nAmount of storage you would need to store all\\\\nthe data.\\\\nHow much memory you might need to store\\\\nfrequently accessed data in cache.\\\\nNetwork bandwidth requirements based on the\\\\nestimated traffic volume and data transfer sizes.\\\\nNote: Check with the interviewer if capacity\\\\nestimation is necessary.\\\\nStep 3. High-Level Design\\\\nSketch out a simple block diagram that outlines the\\\\nmajor system components like: \\\\nClients: User-facing interfaces (eg.. mobile, pc) 1.\\\\nApplication Servers: To process client requests. 2.\\\\nLoad Balancers: To distribute incoming traffic\\\\nacross multiple servers.3.\\\\nServices: Specialized components performing\\\\nspecific functions. 4.\\\\nDatabases: To store user information and\\\\nmetadata.5.\\\\nStorage: To store files, images or videos. 6.\\\\nCaching: To improve latency and reduce load on\\\\nthe database.7.\\\\nMessage Queues: If using asynchronous\\\\ncommunication.8.\\\\nExternal Services: If integrating with third-party\\\\nAPIs (e.g., payment gateways).9.\\\\n\\\\nStep 4. Database Design\\\\nThis steps involve modeling the data, choosing the\\\\nright storage for the system, designing the database\\\\nschema and optimizing the storage and retrieval of\\\\ndata based on the access patterns.\\\\nData Modeling\\\\nIdentify the main data entities or objects that the\\\\nsystem needs to store and manage (e.g., users,\\\\nproducts, orders).\\\\nConsider the relationships between these\\\\nentities and how they interact with each other.\\\\nDetermine the attributes or properties\\\\nassociated with each entity (e.g., a user has an\\\\nemail, name, address).\\\\nIdentify any unique identifiers or primary keys\\\\nfor each entity.\\\\nConsider normalization techniques to ensure\\\\ndata integrity and minimize redundancy.\\\\nEvaluate the requirements and characteristics of\\\\nthe data to determine the most suitable database\\\\ntype.\\\\nConsider factors such as data structure,\\\\nscalability, performance, consistency, and query\\\\npatterns.\\\\nRelational databases (e.g., MySQL, PostgreSQL)\\\\nare suitable for structured data with complex\\\\nrelationships and ACID properties.\\\\nNoSQL databases (e.g., MongoDB, Cassandra) are\\\\nsuitable for unstructured or semi-structured\\\\ndata, high scalability, and eventual consistency.\\\\nConsider using a combination of databases if\\\\ndifferent data subsets have distinct\\\\nrequirements.\\\\nChoose the Right Storage\\\\nStep 5. API Design\\\\nDefine how different components of the system\\\\ninteract with each other and how external clients can\\\\naccess the system's functionality.\\\\nChoose Communication Protocols:\\\\nHTTPS: Commonly used for RESTful APIs and\\\\nweb-based communication.\\\\nWebSockets: Useful for real-time, bidirectional\\\\ncommunication between clients and servers (e.g.,\\\\nchat applications).\\\\ngRPC: Efficient for inter-service communication\\\\nin microservices architectures.\\\\nMessaging Protocols: AMQP, MQTT for\\\\nasynchronous messaging (often used with\\\\nmessage queues).List down the APIs you want to expose to external\\\\nclients based on the problem.\\\\nSelect an appropriate API style based on the\\\\nsystem's requirements and the clients' needs (eg..\\\\nRESTful, GraphQL, RPC).\\\\nStep 6. Dive Deep into Key\\\\nComponents\\\\nYour interviewer will likely want to focus on specific\\\\nareas so pay attention and discuss those things in\\\\nmore detail.\\\\nHere are some more common areas of deep dives:\\\\nDatabases: How would you handle a massive\\\\nincrease in data volume? Discuss sharding\\\\n(splitting data across multiple databases),\\\\nreplication (read/write replicas).\\\\nApplication Servers: How would you add more\\\\nservers behind the load balancer for increased\\\\ntraffic?\\\\nCaching: Where would you add caching to reduce\\\\nlatency and load on the database and how would\\\\nyou deal with cache invalidation?It can differ based on the problem.\\\\nFor example: if you are asked to design a url\\\\nshortener, the interviewer will most likely want you\\\\nto focus on the algorithm for generating short urls.\\\\nAnd, if the problem is about designing a chat\\\\napplication, you should talk about how the messages\\\\nwill be sent and received in real time.\\\\nStep 7. Address Key Concerns\\\\nThis step involves identifying and addressing the\\\\ncore challenges that your system design is likely to\\\\nencounter.\\\\nThese challenges can range from scalability and\\\\nperformance to reliability, security, and cost\\\\nconcerns.\\\\nAddressing Scalability and Performance Concerns:\\\\nScale vertically (Scale-up) by increasing the\\\\ncapacity of individual resources (e.g., CPU,\\\\nmemory, storage).\\\\nScale horizontally (Scale-out) by adding more\\\\nnodes and use load balancers to evenly distribute\\\\nthe traffic among the nodes.\\\\nImplement caching to reduce the load on\\\\nbackend systems and improve response times.\\\\nOptimize database queries using indexes.\\\\nDenormalize data when necessary to reduce join\\\\noperations.\\\\nUse database partitioning and sharding to\\\\nimprove query performance.\\\\nUtilize asynchronous programming models to\\\\nhandle concurrent requests efficiently.\\\\nAddressing Reliability\\\\nAnalyze the system architecture and identify\\\\npotential single point of failures.\\\\nDesign redundancy into the system components\\\\n(multiple load balancers, database replicas) to\\\\neliminate single points of failure.\\\\nConsider geographical redundancy to protect\\\\nagainst regional failures or disasters.\\\\nImplement data replication strategies to ensure\\\\ndata availability and durability.\\\\nImplement circuit breaker patterns to prevent\\\\ncascading failures and protect the system from\\\\noverload.\\\\nImplement retry mechanisms with exponential\\\\nbackoff to handle temporary failures and prevent\\\\noverwhelming the system during recovery.\\\\nImplement comprehensive monitoring and\\\\nalerting systems to detect failures, performance\\\\nissues, and anomalies.\\\\n40\\\\nSYSTEM DESIGN \\\\nINTERVIEW TIPS\\\\n1. Understand the functional and non-functional\\\\nrequirements before designing.\\\\n2. Clearly define the use cases and constraints of the\\\\nsystem.\\\\n3. There is no perfect solution. It\\\\u2019s all about\\\\ntradeoffs.\\\\n4. Assume everything can and will fail. Make it fault\\\\ntolerant.\\\\n5. Keep it simple. Avoid over-engineering.\\\\n6. Design your system for scalability from the ground\\\\nup.\\\\n7. Prefer horizontal scaling over vertical scaling for\\\\nscalability.\\\\n8. Use Load Balancers to ensure high availability and\\\\ndistribute traffic.\\\\n9. Consider using SQL Databases for structured data\\\\nand ACID transactions.\\\\n10. Opt for NoSQL Databases when dealing with\\\\nunstructured data.\\\\n11. Consider using a graph database for highly\\\\nconnected data.\\\\n12. Use Database Sharding to scale SQL databases\\\\nhorizontally.\\\\n13. Use Database Indexing to optimize the read\\\\nqueries in databases.\\\\n14. Assume everything can and will fail. Make it fault\\\\ntolerant.\\\\n15. Use Rate Limiting to prevent system from\\\\noverload and DOS attacks.\\\\n16. Consider using WebSockets for real-time\\\\ncommunication.\\\\n18. Consider using a message queue for\\\\nasynchronous communication.\\\\n19. Implement data partitioning and sharding for\\\\nlarge datasets.\\\\n20. Consider denormalizing databases for read-\\\\nheavy workloads.17. Use Heartbeat Mechanisms to detect failures.\\\\n21. Use bloom filters to check for an item in a large\\\\ndataset quickly.\\\\n22. Use CDNs to reduce latency for a global user\\\\nbase.\\\\n23. Use caching to reduce load on the database and\\\\nimprove response times.\\\\n24. Use write-through cache for write-heavy\\\\napplications.\\\\n25. Use read-through cache for read-heavy\\\\napplications.\\\\n26. Use object storage like S3 for storing large\\\\ndatasets and media files.\\\\n28. Implement Autoscaling to handle traffic spikes\\\\nsmoothly.\\\\n29. Use Asynchronous processing for background\\\\ntasks.\\\\n30. Use batch processing for non-urgent tasks to\\\\noptimize resources.27. Implement Data Replication and Redundancy to\\\\navoid single point of failure.\\\\n31. Make operations idempotent to simplify retry\\\\nlogic and error handling.\\\\n32. Consider using a data lake or data warehouse for\\\\nanalytics and reporting.\\\\n33.  Implement comprehensive logging and\\\\nmonitoring to track the system\\\\u2019s performance and\\\\nhealth.\\\\n34. Implement circuit breakers to prevent a single\\\\nfailing service from bringing down the entire system.\\\\n35.  Implement chaos engineering practices to test\\\\nsystem resilience and find vulnerabilities.\\\\n36. Design for statelessness when possible to\\\\nimprove scalability and simplify architecture.\\\\n37. Use  failover mechanisms to automatically switch\\\\nto a redundant system when a failure is detected.\\\\n38. Distribute your system across different data\\\\ncenters to prevent localized failures.\\\\n39. Use Time-To-Live (TTL) values to automatically\\\\nexpire cached data and reduce staleness.\\\\n40. Pre-populate critical data in the cache to avoid\\\\ncold starts.\\\\n10 MOST COMMON\\\\nSYSTEM DESIGN \\\\nINTERVIEW\\\\nQUESTIONS\\\\n1. Design a URL Shortener like TinyURL\\\\nFunctional Requirements:\\\\nGenerate a unique short URL for a given long URL\\\\nRedirect the user to the original URL when the\\\\nshort URL is accessed\\\\nAllow users to customize their short URLs\\\\n(optional)\\\\nSupport link expiration where URLs are no longer\\\\naccessible after a certain period\\\\nProvide analytics on link usage (optional)\\\\nNon-Functional Requirements:\\\\nHigh availability: The service should be up 99.9%\\\\nof the time.\\\\nLow latency: Url shortening and redirects should\\\\nhappen in milliseconds.\\\\nScalability: The system should handle millions of\\\\nrequests per day.\\\\nDurability: Shortened URLs should work for\\\\nyears.\\\\nSecurity to prevent malicious use, such as\\\\nphishing.\\\\n2. Design a Chat Application like\\\\nWhatsapp\\\\nFunctional Requirements:\\\\nSupport one-on-one and group conversations\\\\nbetween users.\\\\nKeep track of online/offline status of users.\\\\nProvide message delivery statuses (sent,\\\\ndelivered, read).\\\\nSupport multimedia messages (images, videos,\\\\nvoice notes, documents).\\\\nPush notifications for new messages, calls, and\\\\nmentions (optional)\\\\nNon-Functional Requirements:\\\\nReal-time message delivery with minimal latency.\\\\nThe system should handle millions of concurrent\\\\nusers.\\\\nThe system should be highly available. However,\\\\nthe availability can be compromised in the\\\\ninterest of consistency.\\\\nDurability (messages shouldn\\\\u2019t get lost)\\\\n3. Design a social media platform like\\\\nInstagram\\\\nFunctional Requirements:\\\\nUsers can upload and share images and videos.\\\\nUsers can like, comment, and share posts.\\\\nUsers can follow/unfollow other users.\\\\nGenerate and display news feed for users\\\\nshowing posts from people the user follows.\\\\nSupport for tagging other users in posts and\\\\ncomments.\\\\nNon-Functional Requirements:\\\\nHigh availability: The service should be up 99.9%\\\\nof the time.\\\\nLow latency for news feed generation.\\\\nHigh Scalability: The platform should handle\\\\nmillions of concurrent users.\\\\nHigh Durability: User\\\\u2019s uploaded photos and\\\\nvideos should\\\\u2019t get lost.\\\\nEventual Consistency: If a user doesn\\\\u2019t see a\\\\nphoto for sometime, it should be fine.\\\\n4. Design a video streaming service like\\\\nYouTube\\\\nFunctional Requirements:\\\\nUsers can upload videos.\\\\nSupport for adding video titles, descriptions,\\\\ntags, and thumbnails.\\\\nUsers can stream videos on-demand.\\\\nSearch functionality to find videos, channels, and\\\\nplaylists based on keywords.\\\\nUsers can like, dislike, comment on, and share\\\\nvideos.\\\\nService should record view count of videos.\\\\nNon-Functional Requirements:\\\\nHigh availability (e.g., 99.99% uptime) to ensure\\\\nthe service is accessible at all times.\\\\nLow latency: Video streaming should be real-time\\\\nwithout lag\\\\nHigh Scalability: The service should be able to\\\\nscale horizontally to accommodate increasing\\\\nnumbers of users and video content.\\\\nHigh Durability: Uploaded videos shouldn\\\\u2019t get\\\\nlost)\\\\n5. Design an E-commerce Platform like\\\\nAmazon\\\\nFunctional Requirements:\\\\nAllow sellers to list products with details like title,\\\\ndescription, price, images, and specifications.\\\\nUsers can add products to a shopping cart and\\\\nwishlist.\\\\nUsers can search for products, categories, and\\\\nbrands based on keywords\\\\nUsers can place orders for one or multiple\\\\nproducts.\\\\nUsers can rate and review products they have\\\\npurchased.\\\\nNon-Functional Requirements:\\\\nHigh Scalability: The platform should handle\\\\nmillions of users, products, and transactions\\\\nsimultaneously.\\\\nHigh Availability: The service should be up 99.9%\\\\nof the time.\\\\nLow latency for page load times, search queries,\\\\nand checkout processes.\\\\nHigh Durability: All critical data (user data,\\\\nproduct listings, orders) is stored with high\\\\ndurability.\\\\n6. Design a Ride-Sharing Service like\\\\nUber\\\\nFunctional Requirements:\\\\nRiders can see all the nearby available drivers.\\\\nRiders can book a ride by specifying a pickup\\\\nlocation, drop-off location.\\\\nMatch riders with nearby available drivers in real-\\\\ntime.\\\\nReal-time estimation of ride cost and time of\\\\narrival based on distance, traffic, and demand.\\\\nReal-time tracking of the ride both for rider and\\\\ndriver.\\\\nNon-Functional Requirements:\\\\nScalability: The system should scale to handle\\\\nmillions of users and rides simultaneously.\\\\nEnsure low latency for real-time matching, GPS\\\\ntracking, and ride requests.\\\\nEnsure high availability with minimal downtime\\\\n(e.g., 99.9% uptime).\\\\nConsistency: The riders and drivers should have a\\\\nconsistent view of the system.\\\\n7. Design a File Storage Service like\\\\nGoogle Drive\\\\nFunctional Requirements:\\\\nUsers should be able to upload files of various\\\\ntypes and sizes.\\\\nUsers should be able to download files on-\\\\ndemand.\\\\nUsers should be able to share files and folders\\\\nwith other users via links or email invitations.\\\\nAllow users to search for files and folders by\\\\nname, type, content, or metadata.\\\\nSupport synchronization of files across multiple\\\\ndevices.\\\\nNon-Functional Requirements:\\\\nScalability: The system should be able to handle\\\\nmillions of users and billions of files.\\\\nEnsure low-latency file uploads, downloads, and\\\\nsearch operations.\\\\nAvailability: The service should be highly\\\\navailable, with minimal downtime.\\\\nEnsure consistency across all user devices during\\\\nfile synchronization.\\\\nDurability: User\\\\u2019s files should not be lost.\\\\n8. Design a Web Crawler\\\\nFunctional Requirements:\\\\nThe system should be able to fetch URLs from the\\\\nweb efficiently.\\\\nHandle different content types (e.g., text, images,\\\\nmultimedia).\\\\nPrioritize URLs based on specific criteria (e.g.,\\\\nimportance, freshness).\\\\nStore crawled data efficiently in a database or file\\\\nsystem.\\\\nNon-Functional Requirements:\\\\nScalability: The system should scale to handle\\\\nmillions or billions of web pages.\\\\nMinimize latency in fetching and processing web\\\\npages.\\\\nOptimize throughput to maximize the number of\\\\npages crawled per unit of time.\\\\n9. Design a Notification System\\\\nFunctional Requirements:\\\\nSupport for various notification channels such as\\\\nemail, SMS, push notifications (mobile/web), and\\\\nin-app notifications.\\\\nSupport for different types of notifications, such\\\\nas transactional, promotional, and informational.\\\\nAbility to schedule notifications for future\\\\ndelivery.\\\\nAbility to send notifications in bulk, especially for\\\\ncampaigns or mass updates.\\\\nAutomatic retry mechanisms for failed\\\\nnotification deliveries.\\\\nNon-Functional Requirements:\\\\nHigh Scalability: The system should handle\\\\nmillions of notifications per minute, especially\\\\nduring peak times. \\\\nHigh availability (e.g., 99.99% uptime) to ensure\\\\nnotifications are sent without interruption.\\\\nLow latency for sending notifications, especially\\\\nfor real-time and high-priority notifications.\\\\nReliability: The system should ensure reliable\\\\ndelivery of notifications across all supported\\\\nchannels.\\\\n10. Design a Logging and Monitoring\\\\nSystem\\\\nFunctional Requirements:\\\\nCollect logs from various sources such as\\\\napplications, servers, databases, and\\\\nmicroservices.\\\\nSupport for multiple log formats (e.g., JSON,\\\\nplaintext, XML).\\\\nArchive old logs to cost-effective storage (e.g.,\\\\ncloud-based cold storage).\\\\nProvide powerful querying capabilities to filter\\\\nand search logs based on time range, log level,\\\\nsource, and other attributes.\\\\nSet up alerts based on specific log patterns,\\\\nthresholds, or anomalies.\\\\nNon-Functional Requirements:\\\\nScalability: The system should scale horizontally\\\\nto handle increasing volumes of logs, metrics, and\\\\nmonitoring data.\\\\nLow-latency log ingestion and processing to\\\\nensure real-time monitoring.\\\\nHigh availability with minimal downtime (e.g.,\\\\n99.99% uptime) to ensure continuous monitoring.\\\\nDurability: Ensure that log data is stored with\\\\nhigh durability, with replication across multiple\\\\nnodes or data centers.\\", \\"page_count\\": 75, \\"ocr_processed\\": false}}, \\"processing_result\\": {\\"metadata\\": {\\"document_type\\": \\"articles_of_incorporation\\", \\"processing_timestamp\\": \\"2025-08-15T04:06:03.337844+00:00\\", \\"file_hash\\": \\"5e1a7f87312e393c84d97cebb7d85579492d0bf65e3a1ea6edf706b468fb8352\\", \\"extracted_text\\": \\"SYSTEM  D ESIG N \\\\n75 pages guide to ace your next\\\\nSystem Design InterviewASH ISH  PRATAP SING H\\\\nAlgoMaster.ioINTERVIEW  H AND BO O K\\\\nTable of Contents\\\\nFundamentals\\\\n1. Scalability\\\\n2. Availability\\\\n3. Latency vs Throughput\\\\n4. CAP Theorem\\\\n5. Load Balancers\\\\n6. Databases\\\\n7. CDN\\\\n8. Message Queues\\\\n9. Rate Limiting\\\\n10. Database Indexes\\\\n11. Caching\\\\n12. Consistent Hashing\\\\n13. Database Sharding\\\\n14. Consensus Algorithms6\\\\n7\\\\n8\\\\n9\\\\n10\\\\n11\\\\n12\\\\n13\\\\n14\\\\n15\\\\n16\\\\n18\\\\n19\\\\n20\\\\n15. Proxy Servers\\\\n16. Heartbeats\\\\n17. Checksums\\\\n18. Service Discovery\\\\n19. Bloom Filters\\\\n20. Gossip Protocol21\\\\n22\\\\n23\\\\n24\\\\n25\\\\n26\\\\nTrade-offs\\\\n1. Vertical vs Horizontal Scaling\\\\n2. Strong vs Eventual Consistency28\\\\n29\\\\n30\\\\n31\\\\n33\\\\n353. Stateful vs Stateless Design\\\\n4. Read vs Write Through Cache\\\\n5. SQL vs NoSQL\\\\n6. REST vs RPC\\\\n37\\\\n38\\\\n39\\\\n41\\\\n437. Synchronous vs Asynchronous\\\\n8. Batch vs Stream Processing\\\\n9. Long Polling vs WebSockets\\\\n10. Normalization vs Denormalization\\\\n11. TCP vs UDP\\\\nSystem Design Interview Template\\\\n40 System Design Interview TipsArchitectural Patterns\\\\n45\\\\n46\\\\n47\\\\n48\\\\n491. Client-Server Architecture\\\\n2. Microservices Architecture\\\\n3. Serverless Architecture\\\\n4. Event-Driven Architecture\\\\n5. Peer-to-Peer Architecture\\\\n10 most common Interview Questions 656050\\\\n SYSTEM DESIGN \\\\nFUNDAMENTALS\\\\nAs a system grows, the performance starts to \\\\ndegrade unless we adapt it to deal with that growth.\\\\nScalability is the property of a system to handle a \\\\ngrowing amount of load by adding resources to the \\\\nsystem.\\\\nA system that can continuously evolve to support a \\\\ngrowing amount of work is scalable.\\\\n1. Scalability\\\\n2. Availability\\\\nAvailability refers to the proportion of time a system \\\\nis operational and accessible when required.\\\\nAvailability = Uptime / (Uptime + Downtime)\\\\nUptime: The period during which a system is\\\\nfunctional and accessible.\\\\nDowntime: The period during which a system is\\\\nunavailable due to failures, maintenance, or other\\\\nissues.\\\\nAvailability Tiers:\\\\n\\\\n3. Latency vs Throughput\\\\nLatency\\\\nLatency refers to the time it takes for a single \\\\noperation or request to complete.\\\\nLow latency means faster response times and a\\\\nmore responsive system.\\\\nHigh latency can lead to lag and poor user\\\\nexperience.\\\\nThroughput\\\\nThroughput measures the amount of work done or \\\\ndata processed in a given period of time.\\\\nIt is typically expressed in terms of requests per \\\\nsecond (RPS) or transactions per second (TPS).\\\\n4. CAP Theorem\\\\nCAP stands for Consistency, Availability, and \\\\nPartition Tolerance, and the theorem states that:\\\\nIt is impossible for a distributed data store to\\\\nsimultaneously provide all three guarantees.\\\\nConsistency (C): Every read receives the most\\\\nrecent write or an error.\\\\nAvailability (A): Every request (read or write)\\\\nreceives a non-error response, without guarantee\\\\nthat it contains the most recent write.\\\\nPartition Tolerance (P): The system continues to\\\\noperate despite an arbitrary number of messages\\\\nbeing dropped (or delayed) by the network\\\\nbetween nodes.\\\\n5. Load Balancers\\\\nLoad Balancers distribute incoming network traffic\\\\nacross multiple servers to ensure that no single\\\\nserver is overwhelmed.\\\\nPopular Load Balancing Algorithms:\\\\nRound Robin: Distributes requests evenly in\\\\ncircular order.1.\\\\nWeighted Round Robin: Distributes requests\\\\nbased on server capacity weights.2.\\\\nLeast Connections: Sends requests to server with\\\\nfewest active connections.3.\\\\nLeast Response Time: Routes requests to server\\\\nwith fastest response.4.\\\\nIP Hash: Assigns requests based on hashed client\\\\nIP address.5.\\\\n\\\\n6. Databases\\\\nA database is an organized collection of structured\\\\nor unstructured data that can be easily accessed,\\\\nmanaged, and updated.\\\\nTypes of Databases\\\\n1. Relational Databases (RDBMS)\\\\n2. NoSQL Databases\\\\n3. In-Memory Databases\\\\n4. Graph Databases\\\\n5. Time Series Databases\\\\n6. Spatial Databases\\\\nA CDN is a geographically distributed network of\\\\nservers that work together to deliver web content\\\\n(like HTML pages, JavaScript files, stylesheets,\\\\nimages, and videos) to users based on their\\\\ngeographic location.\\\\nThe primary purpose of a CDN is to deliver content\\\\nto end-users with high availability and performance\\\\nby reducing the physical distance between the\\\\nserver and the user.\\\\nWhen a user requests content from a website, the\\\\nCDN redirects the request to the nearest server in its\\\\nnetwork, reducing latency and improving load times.\\\\n7. Content Delivery\\\\nNetwork (CDN)\\\\n8. Message Queues\\\\nA message queue is a communication mechanism\\\\nthat enables different parts of a system to send and\\\\nreceive messages asynchronously.\\\\nProducers can send messages to the queue and\\\\nmove on to other tasks without waiting for\\\\nconsumers to process the messages.\\\\nMultiple consumers can pull messages from the\\\\nqueue, allowing work to be distributed and balanced\\\\nacross different consumers.\\\\n\\\\n9. Rate Limiting\\\\nRate limiting helps protects services from being\\\\noverwhelmed by too many requests from a single\\\\nuser or client.\\\\nRate Limiting Algorithms:\\\\nToken Bucket: Allows bursts traffic within overall\\\\nrate limit.1.\\\\nLeaky Bucket: Smooths traffic flow at constant\\\\nrate.2.\\\\nFixed Window Counter: Limits requests in fixed\\\\ntime intervals.3.\\\\nSliding Window Log: Tracks requests within\\\\nrolling time window.4.\\\\nSliding Window Counter: Smooths rate between\\\\nadjacent fixed windows.5.\\\\n\\\\n10. Database Indexes\\\\nA database index is a super-efficient lookup table\\\\nthat allows a database to find data much faster.\\\\nIt holds the indexed column values along with\\\\npointers to the corresponding rows in the table.\\\\nWithout an index, the database might have to scan\\\\nevery single row in a massive table to find what you\\\\nwant \\\\u2013 a painfully slow process.\\\\nBut, with an index, the database can zero in on the\\\\nexact location of the desired data using the index\\\\u2019s\\\\npointers.\\\\nCaching is a technique used to temporarily store\\\\ncopies of data in high-speed storage layers to reduce\\\\nthe time taken to access data.\\\\nThe primary goal of caching is to improve system\\\\nperformance by reducing latency, offloading the\\\\nmain data store, and providing faster data retrieval.\\\\nCaching Strategies:\\\\nRead-Through Cache: Automatically fetches and\\\\ncaches missing data from source.1.\\\\nWrite-Through Cache: Writes data to cache and\\\\nsource simultaneously.2.\\\\nWrite-Back Cache: Writes to cache first, updates\\\\nsource later.3.\\\\nCache-Aside: Application manages data retrieval\\\\nand cache population.4.\\\\n11. Caching\\\\n\\\\nCaching Eviction Policies:\\\\nLeast Recently Used (LRU): Removes the item\\\\nthat hasn't been accessed for the longest time.1.\\\\nLeast Frequently Used (LFU): Discards items with\\\\nthe lowest access frequency over time.2.\\\\nFirst In, First Out (FIFO): Removes the oldest\\\\nitem, regardless of its usage frequency.3.\\\\nTime-to-Live (TTL): Automatically removes items\\\\nafter a predefined expiration time has passed.4.\\\\nConsistent Hashing is a special kind of hashing\\\\ntechnique that allows for efficient distribution of\\\\ndata across a cluster of nodes.\\\\nConsistent hashing ensures that only a small portion\\\\nof the data needs to be reassigned when nodes are\\\\nadded or removed.\\\\n12. Consistent Hashing\\\\nHow Does it Work?\\\\nHash Space: Imagine a fixed circular space or \\\\\\"ring\\\\\\"\\\\nranging from 0 to 2^n-1.1.\\\\nMapping Servers: Each server is mapped to one or\\\\nmore points on this ring using a hash function.2.\\\\nMapping Data: Each data item is also hashed onto\\\\nthe ring.3.\\\\nData Assignment: A data item is stored on the first\\\\nserver encountered while moving clockwise on the\\\\nring from the item's position.4.\\\\n\\\\n13. Database Sharding\\\\nDatabase sharding is a horizontal scaling technique\\\\nused to split a large database into smaller,\\\\nindependent pieces called shards.\\\\nThese shards are then distributed across multiple\\\\nservers or nodes, each responsible for handling a\\\\nspecific subset of the data.\\\\nBy distributing the data across multiple nodes,\\\\nsharding can significantly reduce the load on any\\\\nsingle server, resulting in faster query execution and\\\\nimproved overall system performance.\\\\n\\\\nIn a distributed system, nodes need to work together\\\\nto maintain a consistent state. \\\\nHowever, due to the inherent challenges like network\\\\nlatency, node failures, and asynchrony, achieving\\\\nthis consistency is not straightforward. \\\\nConsensus algorithms address these challenges by\\\\nensuring that all participating nodes agree on the\\\\nsame state or sequence of events, even when some\\\\nnodes might fail or act maliciously.\\\\n14. Consensus Algorithms\\\\nPopular Consensus Algorithms\\\\n1. Paxos: Paxos works by electing a leader that\\\\nproposes a value, which is then accepted by a\\\\nmajority of the nodes.\\\\n2. Raft: Raft works by designating one node as the\\\\nleader to manage log replication and ensure\\\\nconsistency across the cluster.\\\\n\\\\n15. Proxy Servers\\\\nA proxy server acts as a gateway between you and\\\\nthe internet. It's an intermediary server separating\\\\nend users from the websites they browse.\\\\n2 Common types of Proxy Servers:\\\\nForward Proxies: Sits in front of a client and\\\\nforwards requests to the internet on behalf of the\\\\nclient.1.\\\\nReverse Proxies: Sits in front of a web server and\\\\nforwards requests from clients to the server.2.\\\\n\\\\n16. HeartBeats\\\\nIn distributed systems, a heartbeat is a periodic\\\\nmessage sent from one component to another to\\\\nmonitor each other's health and status.\\\\nWithout a heartbeat mechanism, it's hard to quickly\\\\ndetect failures in a distributed system, leading to:\\\\nDelayed fault detection and recovery\\\\nIncreased downtime and errors\\\\nDecreased overall system reliability\\\\n17. Checksums\\\\nA checksum is a unique fingerprint attached to the\\\\ndata before it's transmitted. \\\\nWhen the data arrives at the recipient's end, the\\\\nfingerprint is recalculated to ensure it matches the\\\\noriginal one.\\\\nIf the checksum of a piece of data matches the\\\\nexpected value, you can be confident that the data\\\\nhasn't been modified or damaged.\\\\n\\\\n18. Service Discovery\\\\nService discovery is a mechanism that allows services\\\\nin a distributed system to find and communicate with\\\\neach other dynamically. \\\\nIt hides the complex details of where services are\\\\nlocated, so they can interact without knowing each\\\\nother's exact network spots.\\\\nService discovery registers and maintains a record of\\\\nall your services in a service registry. \\\\nThis service registry acts as a single source of truth\\\\nthat allows your services to query and communicate\\\\nwith each other.\\\\n\\\\nA Bloom filter is a probabilistic data structure that\\\\nis primarily used to determine whether an element\\\\nis definitely not in a set or possibly in the set.\\\\nHow Does It Work?\\\\nSetup: Start with a bit array of m bits, all set to\\\\n0, and k different hash functions.1.\\\\nAdding an element: To add an element, feed it\\\\nto each of the k hash functions to get k array\\\\npositions. Set the bits at all these positions to 1.2.\\\\nQuerying: To query for an element, feed it to\\\\neach of the k hash functions to get k array\\\\npositions. If any of the bits at these positions\\\\nare 0, the element is definitely not in the set. If\\\\nall are 1, then either the element is in the set, or\\\\nwe have a false positive.3.\\\\n19. Bloom Filters\\\\nGossip Protocol is a decentralized communication\\\\nprotocol used in distributed systems to spread\\\\ninformation across all nodes.\\\\nIt is inspired by the way humans share news by word-\\\\nof-mouth, where each person who learns the\\\\ninformation shares it with others, leading to\\\\nwidespread dissemination.\\\\n20. Gossip Protocol\\\\nHow does it work?\\\\nInitialization: A node in the system starts with a\\\\npiece of information, known as a \\\\\\"gossip.\\\\\\"1.\\\\nGossip Exchange: At regular intervals, each node\\\\nrandomly selects another node and shares its\\\\ncurrent gossip. The receiving node then merges\\\\nthe received gossip with its own.2.\\\\nPropagation: The process repeats, with each node\\\\nspreading the gossip to others.3.\\\\nConvergence: Eventually, every node in the\\\\nnetwork will have received the gossip, ensuring\\\\nthat all nodes have consistent information.4.\\\\n\\\\nSYSTEM DESIGN\\\\nTRADE-OFFS\\\\n1. Vertical vs Horizontal Scaling\\\\nVertical scaling involves boosting the power of an\\\\nexisting machine (eg.. CPU, RAM, Storage) to handle\\\\nincreased loads.\\\\nScaling vertically is simpler but there's a physical\\\\nlimit to how much you can upgrade a single machine\\\\nand it introduces a single point of failure.\\\\nHorizontal scaling involves adding more servers or\\\\nnodes to the system to distribute the load across\\\\nmultiple machines.\\\\nScaling horizontally allows for almost limitless\\\\nscaling but brings complexity of managing\\\\ndistributed systems.\\\\n\\\\n2. Strong vs Eventual Consistency\\\\nStrong consistency ensures that any read operation\\\\nreturns the most recent write for a given piece of\\\\ndata.\\\\nThis means that once a write is acknowledged, all\\\\nsubsequent reads will reflect that write\\\\nEventual consistency ensures that, given enough\\\\ntime, all nodes in the system will converge to the\\\\nsame value. \\\\nHowever, there are no guarantees about when this\\\\nconvergence will occur.\\\\n3. Stateful vs Stateless Design\\\\nIn a stateful design, the system remembers client\\\\ndata from one request to the next.\\\\nIt maintains a record of the client's state, which can\\\\ninclude session information, transaction details, or\\\\nany other data relevant to the ongoing interaction.\\\\nStateless design treats each request as an\\\\nindependent transaction. The server does not store\\\\nany information about the client's state between\\\\nrequests.\\\\nEach request must contain all the information\\\\nnecessary to understand and process it.\\\\n\\\\n4. Read-Through vs  Write-Through\\\\nCache\\\\n\\\\nA Read-Through cache sits between your application\\\\nand your data store.\\\\nWhen your application requests data, it first checks\\\\nthe cache.\\\\nIf the data is found in the cache (a cache hit), it's\\\\nreturned to the application.\\\\nIf the data is not in the cache (a cache miss), the\\\\ncache itself is responsible for loading the data from\\\\nthe data store, caching it, and then returning it to the\\\\napplication.\\\\nIn a Write-Through cache strategy, data is written\\\\ninto the cache and the corresponding database\\\\nsimultaneously.\\\\nEvery write operation writes data to both the cache\\\\nand the data store.\\\\nThe write operation is only considered complete\\\\nwhen both writes are successful.\\\\n5. SQL vs NoSQL\\\\nSQL databases use structured query language and\\\\nhave a predefined schema. They're ideal for:\\\\nComplex queries: SQL is powerful for querying\\\\ncomplex relationships between data.\\\\nACID compliance: Ensures data validity in high-\\\\nstake transactions (e.g., financial systems).\\\\nStructured data: When your data structure is\\\\nunlikely to change.\\\\nExamples: MySQL, PostgreSQL, Oracle\\\\nNoSQL databases are more flexible and scalable.\\\\nThey're best for:\\\\nBig Data: Can handle large volumes of structured\\\\nand unstructured data.\\\\nRapid development: Schema-less nature allows\\\\nfor quicker iterations.\\\\nScalability: Easier to scale horizontally.\\\\nExamples: MongoDB, Cassandra, Redis\\\\n6. REST vs  RPC\\\\nWhen designing APIs, two popular architectural\\\\nstyles often come into consideration: REST\\\\n(Representational State Transfer) and RPC (Remote\\\\nProcedure Call). Both have their strengths and ideal\\\\nuse cases. Let's dive into their key differences to help\\\\nyou choose the right one for your project.\\\\nREST (Representational State Transfer)\\\\nREST is an architectural style that uses HTTP\\\\nmethods to interact with resources.\\\\nKey characteristics:\\\\nStateless: Each request contains all necessary\\\\ninformation\\\\nResource-based: Uses URLs to represent\\\\nresources\\\\nUses standard HTTP methods (GET, POST, PUT,\\\\nDELETE)\\\\nTypically returns data in JSON or XML format\\\\nRPC (Remote Procedure Call)\\\\nRPC is a protocol that one program can use to\\\\nrequest a service from a program located on another\\\\ncomputer in a network.\\\\nKey characteristics:\\\\nAction-based: Focuses on operations or actions\\\\nCan use various protocols (HTTP, TCP, etc.)\\\\nOften uses custom methods\\\\nTypically returns custom data formats\\\\n7. Synchronous vs  Asynchronous\\\\n\\\\ud83d\\\\udd39 Synchronous Processing:\\\\nTasks are executed sequentially.\\\\nMakes it easier to reason about code and handle\\\\ndependencies.\\\\nUsed in scenarios where tasks must be completed\\\\nin order like reading a file line by line.\\\\n\\\\ud83d\\\\udd39 Asynchronous Processing:\\\\nTasks are executed concurrently.\\\\nImproves responsiveness and performance,\\\\nespecially in I/O-bound operations\\\\nUsed when you need to handle multiple tasks\\\\nsimultaneously without blocking the main thread.\\\\nlike background processing jobs.\\\\n8. Batch vs  Stream Processing\\\\n\\\\ud83d\\\\udd39 Batch Processing:\\\\nProcess large volumes of data at once, typically at\\\\nscheduled intervals.\\\\nEfficient for handling massive datasets, ideal for\\\\ntasks like reporting or data warehousing.\\\\nHigh Latency -  results are available only after the\\\\nentire batch is processed.\\\\nExamples: ETL jobs, data aggregation, periodic\\\\nbackups.\\\\n\\\\ud83d\\\\udd39 Stream Processing:\\\\nProcess data in real-time as it arrives.\\\\nPerfect for real-time analytics, monitoring, and\\\\nalerting systems.\\\\nMinimal latency since data is processed within\\\\nmilliseconds or seconds of arrival.\\\\nExamples: Real-time fraud detection, live data\\\\nfeeds, IoT applications.\\\\n9. Long Polling vs WebSockets\\\\n\\\\nWebsokcet establishes a persistent, full-duplex\\\\nconnection between the client and server,\\\\nallowing real-time data exchange without the\\\\noverhead of HTTP requests.\\\\nUnlike the traditional HTTP protocol, where the\\\\nclient sends a request to the server and waits for\\\\na response, WebSockets allow both the client\\\\nand server to send messages to each other\\\\nindependently and continuously after the\\\\nconnection is established.In a Long Polling connection, the client repeatedly\\\\nrequests updates from the server at regular\\\\nintervals. \\\\nIf the server has new data, it sends a response\\\\nimmediately; otherwise, it holds the connection until\\\\ndata is available. \\\\nThis can lead to Increased latency and higher server\\\\nload due to frequent requests, even when no data is\\\\navailable.\\\\n10. Normalization vs Denormalization\\\\nNormalization in database design involves splitting\\\\nup data into related tables to ensure each piece of\\\\ninformation is stored only once.\\\\nIt aims to reduce redundancy and improve data\\\\nintegrity.\\\\nExample: A customer database can have two\\\\nseparate tables: one for customer details and\\\\nanother for orders, avoiding duplication of customer\\\\ninformation for each order.\\\\nDenormalization is the process of combining data\\\\nback into fewer tables to improve query\\\\nperformance. \\\\nThis often means introducing redundancy (duplicate\\\\ninformation) back into your database.\\\\nExample: A blog website can store the latest\\\\ncomments with the posts in the same table\\\\n(denormalized) to speed up the display of post and\\\\ncomments, instead of storing them separately\\\\n(normalized).\\\\n11. TCP vs UDP\\\\nWhen it comes to data transmission over the\\\\ninternet, two key protocols are at the forefront: TCP\\\\nand UDP. \\\\n\\\\ud83d\\\\udd39 TCP (Transmission Control Protocol):\\\\nReliable: Ensures all data packets arrive in order\\\\nand are error-free.\\\\nConnection-Oriented: Establishes a connection\\\\nbefore data transfer, making it ideal for tasks\\\\nwhere accuracy is crucial (e.g., web browsing, file\\\\ntransfers).\\\\nSlower: The overhead of managing connections\\\\nand ensuring reliability can introduce latency.\\\\n\\\\ud83d\\\\udd39 UDP (User Datagram Protocol):\\\\nFaster: Minimal overhead allows for quick data\\\\ntransfer, perfect for time-sensitive applications.\\\\nConnectionless: No formal connection setup;\\\\ndata is sent without guarantees, making it ideal\\\\nfor real-time applications (e.g., video streaming,\\\\nonline gaming).\\\\nUnreliable: No error-checking or ordering, so\\\\nsome data packets might be lost or arrive out of\\\\norder.\\\\nARCHITECTURAL\\\\nPATTERNS\\\\nIn this model, the system is divided into two main\\\\ncomponents: the client and the server.\\\\nClient: The client is typically the user-facing part\\\\nof the system, such as a web browser, mobile\\\\napp, or desktop application. Clients send\\\\nrequests to the server and display the results to\\\\nthe user.\\\\nServer: The server processes client requests,\\\\nmanages resources like databases, and sends the\\\\nrequired data or services back to the client.\\\\n1. Client-Server Architecture\\\\n\\\\n2. Microservices Architecture\\\\nMicroservices architecture is an approach to\\\\ndesigning a system as a collection of loosely\\\\ncoupled, independently deployable services. \\\\nEach microservice corresponds to a specific\\\\nbusiness function and communicates with other\\\\nservices via lightweight protocols, often HTTP/REST\\\\nor messaging queues.\\\\nServices are small, focused on doing one thing well\\\\nand each service has its own database to ensure\\\\nloose coupling.\\\\n3. Serverless Architecture\\\\nServerless architecture abstracts away the\\\\nunderlying infrastructure, allowing developers to\\\\nfocus solely on writing code. \\\\nIn a serverless model, the cloud provider\\\\nautomatically manages the infrastructure, scaling,\\\\nand server maintenance. \\\\nDevelopers deploy functions that are triggered by\\\\nevents, and they are billed only for the compute time\\\\nconsumed.\\\\nIdeal for applications that react to events, such as\\\\nprocessing files, triggering workflows, or handling\\\\nreal-time data streams.\\\\n4. Event-Driven Architecture\\\\nEvent-Driven Architecture (EDA) is a design pattern\\\\nin which the system responds to events, or changes\\\\nin state, that are propagated throughout the system. \\\\nIn EDA, components are decoupled and\\\\ncommunicate through events, which are typically\\\\nhandled asynchronously. \\\\nEvents can be processed in parallel by multiple\\\\nconsumers, allowing the system to scale efficiently.\\\\n\\\\n5. Peer-to-Peer (P2P) Architecture\\\\nP2P architecture is a decentralized model where\\\\neach node, or \\\\\\"peer,\\\\\\" in the network has equal\\\\nresponsibilities and capabilities.\\\\nUnlike the client-server model, there is no central\\\\nserver; instead, each peer can act as both a client\\\\nand a server, sharing resources and data directly\\\\nwith other peers. \\\\nP2P networks are known for their resilience and\\\\nscalability since there is no central point of failure\\\\nand system can scale easily as new peers join the\\\\nnetwork.\\\\n\\\\nSYSTEM DESIGN\\\\nINTERVIEW\\\\nTEMPLATE\\\\nA step-by-step guide to \\\\nSystem Design Interviews\\\\nStep 1. Clarify Requirements\\\\nFunctional Requirements:\\\\nWhat are the core features that the system\\\\nshould support?\\\\nWho are the users (eg.. customers, internal teams\\\\netc.)?\\\\nHow will users interact with the system (eg.. web,\\\\nmobile app, API, etc.)?\\\\nWhat are the key data types the system must\\\\nhandle (text, images, structured data, etc). \\\\nAre there any external systems or third-party\\\\nservices the system needs to integrate with?\\\\nNon-Functional Requirements:\\\\nIs the system read heavy or write heavy and\\\\nwhat\\\\u2019s the read-to-write ratio?\\\\nCan the system have some downtime, or does it\\\\nneed to be highly available?\\\\nAre there any specific latency requirements?\\\\nHow critical is data consistency?\\\\nShould we rate limit the users to prevent abuse of\\\\nthe system?Start by clarifying functional and non-functional\\\\nrequirements. Here are things to consider:\\\\nStep 2. Capacity Estimation\\\\nEstimate capacity to get an overall idea about how\\\\nbig a system you are going to design.\\\\nThis can include things like:\\\\nHow many users are expected to use the system\\\\ndaily and monthly and maximum concurrent\\\\nusers during peak hours?\\\\nExpected read/write requests per second.\\\\nAmount of storage you would need to store all\\\\nthe data.\\\\nHow much memory you might need to store\\\\nfrequently accessed data in cache.\\\\nNetwork bandwidth requirements based on the\\\\nestimated traffic volume and data transfer sizes.\\\\nNote: Check with the interviewer if capacity\\\\nestimation is necessary.\\\\nStep 3. High-Level Design\\\\nSketch out a simple block diagram that outlines the\\\\nmajor system components like: \\\\nClients: User-facing interfaces (eg.. mobile, pc) 1.\\\\nApplication Servers: To process client requests. 2.\\\\nLoad Balancers: To distribute incoming traffic\\\\nacross multiple servers.3.\\\\nServices: Specialized components performing\\\\nspecific functions. 4.\\\\nDatabases: To store user information and\\\\nmetadata.5.\\\\nStorage: To store files, images or videos. 6.\\\\nCaching: To improve latency and reduce load on\\\\nthe database.7.\\\\nMessage Queues: If using asynchronous\\\\ncommunication.8.\\\\nExternal Services: If integrating with third-party\\\\nAPIs (e.g., payment gateways).9.\\\\n\\\\nStep 4. Database Design\\\\nThis steps involve modeling the data, choosing the\\\\nright storage for the system, designing the database\\\\nschema and optimizing the storage and retrieval of\\\\ndata based on the access patterns.\\\\nData Modeling\\\\nIdentify the main data entities or objects that the\\\\nsystem needs to store and manage (e.g., users,\\\\nproducts, orders).\\\\nConsider the relationships between these\\\\nentities and how they interact with each other.\\\\nDetermine the attributes or properties\\\\nassociated with each entity (e.g., a user has an\\\\nemail, name, address).\\\\nIdentify any unique identifiers or primary keys\\\\nfor each entity.\\\\nConsider normalization techniques to ensure\\\\ndata integrity and minimize redundancy.\\\\nEvaluate the requirements and characteristics of\\\\nthe data to determine the most suitable database\\\\ntype.\\\\nConsider factors such as data structure,\\\\nscalability, performance, consistency, and query\\\\npatterns.\\\\nRelational databases (e.g., MySQL, PostgreSQL)\\\\nare suitable for structured data with complex\\\\nrelationships and ACID properties.\\\\nNoSQL databases (e.g., MongoDB, Cassandra) are\\\\nsuitable for unstructured or semi-structured\\\\ndata, high scalability, and eventual consistency.\\\\nConsider using a combination of databases if\\\\ndifferent data subsets have distinct\\\\nrequirements.\\\\nChoose the Right Storage\\\\nStep 5. API Design\\\\nDefine how different components of the system\\\\ninteract with each other and how external clients can\\\\naccess the system's functionality.\\\\nChoose Communication Protocols:\\\\nHTTPS: Commonly used for RESTful APIs and\\\\nweb-based communication.\\\\nWebSockets: Useful for real-time, bidirectional\\\\ncommunication between clients and servers (e.g.,\\\\nchat applications).\\\\ngRPC: Efficient for inter-service communication\\\\nin microservices architectures.\\\\nMessaging Protocols: AMQP, MQTT for\\\\nasynchronous messaging (often used with\\\\nmessage queues).List down the APIs you want to expose to external\\\\nclients based on the problem.\\\\nSelect an appropriate API style based on the\\\\nsystem's requirements and the clients' needs (eg..\\\\nRESTful, GraphQL, RPC).\\\\nStep 6. Dive Deep into Key\\\\nComponents\\\\nYour interviewer will likely want to focus on specific\\\\nareas so pay attention and discuss those things in\\\\nmore detail.\\\\nHere are some more common areas of deep dives:\\\\nDatabases: How would you handle a massive\\\\nincrease in data volume? Discuss sharding\\\\n(splitting data across multiple databases),\\\\nreplication (read/write replicas).\\\\nApplication Servers: How would you add more\\\\nservers behind the load balancer for increased\\\\ntraffic?\\\\nCaching: Where would you add caching to reduce\\\\nlatency and load on the database and how would\\\\nyou deal with cache invalidation?It can differ based on the problem.\\\\nFor example: if you are asked to design a url\\\\nshortener, the interviewer will most likely want you\\\\nto focus on the algorithm for generating short urls.\\\\nAnd, if the problem is about designing a chat\\\\napplication, you should talk about how the messages\\\\nwill be sent and received in real time.\\\\nStep 7. Address Key Concerns\\\\nThis step involves identifying and addressing the\\\\ncore challenges that your system design is likely to\\\\nencounter.\\\\nThese challenges can range from scalability and\\\\nperformance to reliability, security, and cost\\\\nconcerns.\\\\nAddressing Scalability and Performance Concerns:\\\\nScale vertically (Scale-up) by increasing the\\\\ncapacity of individual resources (e.g., CPU,\\\\nmemory, storage).\\\\nScale horizontally (Scale-out) by adding more\\\\nnodes and use load balancers to evenly distribute\\\\nthe traffic among the nodes.\\\\nImplement caching to reduce the load on\\\\nbackend systems and improve response times.\\\\nOptimize database queries using indexes.\\\\nDenormalize data when necessary to reduce join\\\\noperations.\\\\nUse database partitioning and sharding to\\\\nimprove query performance.\\\\nUtilize asynchronous programming models to\\\\nhandle concurrent requests efficiently.\\\\nAddressing Reliability\\\\nAnalyze the system architecture and identify\\\\npotential single point of failures.\\\\nDesign redundancy into the system components\\\\n(multiple load balancers, database replicas) to\\\\neliminate single points of failure.\\\\nConsider geographical redundancy to protect\\\\nagainst regional failures or disasters.\\\\nImplement data replication strategies to ensure\\\\ndata availability and durability.\\\\nImplement circuit breaker patterns to prevent\\\\ncascading failures and protect the system from\\\\noverload.\\\\nImplement retry mechanisms with exponential\\\\nbackoff to handle temporary failures and prevent\\\\noverwhelming the system during recovery.\\\\nImplement comprehensive monitoring and\\\\nalerting systems to detect failures, performance\\\\nissues, and anomalies.\\\\n40\\\\nSYSTEM DESIGN \\\\nINTERVIEW TIPS\\\\n1. Understand the functional and non-functional\\\\nrequirements before designing.\\\\n2. Clearly define the use cases and constraints of the\\\\nsystem.\\\\n3. There is no perfect solution. It\\\\u2019s all about\\\\ntradeoffs.\\\\n4. Assume everything can and will fail. Make it fault\\\\ntolerant.\\\\n5. Keep it simple. Avoid over-engineering.\\\\n6. Design your system for scalability from the ground\\\\nup.\\\\n7. Prefer horizontal scaling over vertical scaling for\\\\nscalability.\\\\n8. Use Load Balancers to ensure high availability and\\\\ndistribute traffic.\\\\n9. Consider using SQL Databases for structured data\\\\nand ACID transactions.\\\\n10. Opt for NoSQL Databases when dealing with\\\\nunstructured data.\\\\n11. Consider using a graph database for highly\\\\nconnected data.\\\\n12. Use Database Sharding to scale SQL databases\\\\nhorizontally.\\\\n13. Use Database Indexing to optimize the read\\\\nqueries in databases.\\\\n14. Assume everything can and will fail. Make it fault\\\\ntolerant.\\\\n15. Use Rate Limiting to prevent system from\\\\noverload and DOS attacks.\\\\n16. Consider using WebSockets for real-time\\\\ncommunication.\\\\n18. Consider using a message queue for\\\\nasynchronous communication.\\\\n19. Implement data partitioning and sharding for\\\\nlarge datasets.\\\\n20. Consider denormalizing databases for read-\\\\nheavy workloads.17. Use Heartbeat Mechanisms to detect failures.\\\\n21. Use bloom filters to check for an item in a large\\\\ndataset quickly.\\\\n22. Use CDNs to reduce latency for a global user\\\\nbase.\\\\n23. Use caching to reduce load on the database and\\\\nimprove response times.\\\\n24. Use write-through cache for write-heavy\\\\napplications.\\\\n25. Use read-through cache for read-heavy\\\\napplications.\\\\n26. Use object storage like S3 for storing large\\\\ndatasets and media files.\\\\n28. Implement Autoscaling to handle traffic spikes\\\\nsmoothly.\\\\n29. Use Asynchronous processing for background\\\\ntasks.\\\\n30. Use batch processing for non-urgent tasks to\\\\noptimize resources.27. Implement Data Replication and Redundancy to\\\\navoid single point of failure.\\\\n31. Make operations idempotent to simplify retry\\\\nlogic and error handling.\\\\n32. Consider using a data lake or data warehouse for\\\\nanalytics and reporting.\\\\n33.  Implement comprehensive logging and\\\\nmonitoring to track the system\\\\u2019s performance and\\\\nhealth.\\\\n34. Implement circuit breakers to prevent a single\\\\nfailing service from bringing down the entire system.\\\\n35.  Implement chaos engineering practices to test\\\\nsystem resilience and find vulnerabilities.\\\\n36. Design for statelessness when possible to\\\\nimprove scalability and simplify architecture.\\\\n37. Use  failover mechanisms to automatically switch\\\\nto a redundant system when a failure is detected.\\\\n38. Distribute your system across different data\\\\ncenters to prevent localized failures.\\\\n39. Use Time-To-Live (TTL) values to automatically\\\\nexpire cached data and reduce staleness.\\\\n40. Pre-populate critical data in the cache to avoid\\\\ncold starts.\\\\n10 MOST COMMON\\\\nSYSTEM DESIGN \\\\nINTERVIEW\\\\nQUESTIONS\\\\n1. Design a URL Shortener like TinyURL\\\\nFunctional Requirements:\\\\nGenerate a unique short URL for a given long URL\\\\nRedirect the user to the original URL when the\\\\nshort URL is accessed\\\\nAllow users to customize their short URLs\\\\n(optional)\\\\nSupport link expiration where URLs are no longer\\\\naccessible after a certain period\\\\nProvide analytics on link usage (optional)\\\\nNon-Functional Requirements:\\\\nHigh availability: The service should be up 99.9%\\\\nof the time.\\\\nLow latency: Url shortening and redirects should\\\\nhappen in milliseconds.\\\\nScalability: The system should handle millions of\\\\nrequests per day.\\\\nDurability: Shortened URLs should work for\\\\nyears.\\\\nSecurity to prevent malicious use, such as\\\\nphishing.\\\\n2. Design a Chat Application like\\\\nWhatsapp\\\\nFunctional Requirements:\\\\nSupport one-on-one and group conversations\\\\nbetween users.\\\\nKeep track of online/offline status of users.\\\\nProvide message delivery statuses (sent,\\\\ndelivered, read).\\\\nSupport multimedia messages (images, videos,\\\\nvoice notes, documents).\\\\nPush notifications for new messages, calls, and\\\\nmentions (optional)\\\\nNon-Functional Requirements:\\\\nReal-time message delivery with minimal latency.\\\\nThe system should handle millions of concurrent\\\\nusers.\\\\nThe system should be highly available. However,\\\\nthe availability can be compromised in the\\\\ninterest of consistency.\\\\nDurability (messages shouldn\\\\u2019t get lost)\\\\n3. Design a social media platform like\\\\nInstagram\\\\nFunctional Requirements:\\\\nUsers can upload and share images and videos.\\\\nUsers can like, comment, and share posts.\\\\nUsers can follow/unfollow other users.\\\\nGenerate and display news feed for users\\\\nshowing posts from people the user follows.\\\\nSupport for tagging other users in posts and\\\\ncomments.\\\\nNon-Functional Requirements:\\\\nHigh availability: The service should be up 99.9%\\\\nof the time.\\\\nLow latency for news feed generation.\\\\nHigh Scalability: The platform should handle\\\\nmillions of concurrent users.\\\\nHigh Durability: User\\\\u2019s uploaded photos and\\\\nvideos should\\\\u2019t get lost.\\\\nEventual Consistency: If a user doesn\\\\u2019t see a\\\\nphoto for sometime, it should be fine.\\\\n4. Design a video streaming service like\\\\nYouTube\\\\nFunctional Requirements:\\\\nUsers can upload videos.\\\\nSupport for adding video titles, descriptions,\\\\ntags, and thumbnails.\\\\nUsers can stream videos on-demand.\\\\nSearch functionality to find videos, channels, and\\\\nplaylists based on keywords.\\\\nUsers can like, dislike, comment on, and share\\\\nvideos.\\\\nService should record view count of videos.\\\\nNon-Functional Requirements:\\\\nHigh availability (e.g., 99.99% uptime) to ensure\\\\nthe service is accessible at all times.\\\\nLow latency: Video streaming should be real-time\\\\nwithout lag\\\\nHigh Scalability: The service should be able to\\\\nscale horizontally to accommodate increasing\\\\nnumbers of users and video content.\\\\nHigh Durability: Uploaded videos shouldn\\\\u2019t get\\\\nlost)\\\\n5. Design an E-commerce Platform like\\\\nAmazon\\\\nFunctional Requirements:\\\\nAllow sellers to list products with details like title,\\\\ndescription, price, images, and specifications.\\\\nUsers can add products to a shopping cart and\\\\nwishlist.\\\\nUsers can search for products, categories, and\\\\nbrands based on keywords\\\\nUsers can place orders for one or multiple\\\\nproducts.\\\\nUsers can rate and review products they have\\\\npurchased.\\\\nNon-Functional Requirements:\\\\nHigh Scalability: The platform should handle\\\\nmillions of users, products, and transactions\\\\nsimultaneously.\\\\nHigh Availability: The service should be up 99.9%\\\\nof the time.\\\\nLow latency for page load times, search queries,\\\\nand checkout processes.\\\\nHigh Durability: All critical data (user data,\\\\nproduct listings, orders) is stored with high\\\\ndurability.\\\\n6. Design a Ride-Sharing Service like\\\\nUber\\\\nFunctional Requirements:\\\\nRiders can see all the nearby available drivers.\\\\nRiders can book a ride by specifying a pickup\\\\nlocation, drop-off location.\\\\nMatch riders with nearby available drivers in real-\\\\ntime.\\\\nReal-time estimation of ride cost and time of\\\\narrival based on distance, traffic, and demand.\\\\nReal-time tracking of the ride both for rider and\\\\ndriver.\\\\nNon-Functional Requirements:\\\\nScalability: The system should scale to handle\\\\nmillions of users and rides simultaneously.\\\\nEnsure low latency for real-time matching, GPS\\\\ntracking, and ride requests.\\\\nEnsure high availability with minimal downtime\\\\n(e.g., 99.9% uptime).\\\\nConsistency: The riders and drivers should have a\\\\nconsistent view of the system.\\\\n7. Design a File Storage Service like\\\\nGoogle Drive\\\\nFunctional Requirements:\\\\nUsers should be able to upload files of various\\\\ntypes and sizes.\\\\nUsers should be able to download files on-\\\\ndemand.\\\\nUsers should be able to share files and folders\\\\nwith other users via links or email invitations.\\\\nAllow users to search for files and folders by\\\\nname, type, content, or metadata.\\\\nSupport synchronization of files across multiple\\\\ndevices.\\\\nNon-Functional Requirements:\\\\nScalability: The system should be able to handle\\\\nmillions of users and billions of files.\\\\nEnsure low-latency file uploads, downloads, and\\\\nsearch operations.\\\\nAvailability: The service should be highly\\\\navailable, with minimal downtime.\\\\nEnsure consistency across all user devices during\\\\nfile synchronization.\\\\nDurability: User\\\\u2019s files should not be lost.\\\\n8. Design a Web Crawler\\\\nFunctional Requirements:\\\\nThe system should be able to fetch URLs from the\\\\nweb efficiently.\\\\nHandle different content types (e.g., text, images,\\\\nmultimedia).\\\\nPrioritize URLs based on specific criteria (e.g.,\\\\nimportance, freshness).\\\\nStore crawled data efficiently in a database or file\\\\nsystem.\\\\nNon-Functional Requirements:\\\\nScalability: The system should scale to handle\\\\nmillions or billions of web pages.\\\\nMinimize latency in fetching and processing web\\\\npages.\\\\nOptimize throughput to maximize the number of\\\\npages crawled per unit of time.\\\\n9. Design a Notification System\\\\nFunctional Requirements:\\\\nSupport for various notification channels such as\\\\nemail, SMS, push notifications (mobile/web), and\\\\nin-app notifications.\\\\nSupport for different types of notifications, such\\\\nas transactional, promotional, and informational.\\\\nAbility to schedule notifications for future\\\\ndelivery.\\\\nAbility to send notifications in bulk, especially for\\\\ncampaigns or mass updates.\\\\nAutomatic retry mechanisms for failed\\\\nnotification deliveries.\\\\nNon-Functional Requirements:\\\\nHigh Scalability: The system should handle\\\\nmillions of notifications per minute, especially\\\\nduring peak times. \\\\nHigh availability (e.g., 99.99% uptime) to ensure\\\\nnotifications are sent without interruption.\\\\nLow latency for sending notifications, especially\\\\nfor real-time and high-priority notifications.\\\\nReliability: The system should ensure reliable\\\\ndelivery of notifications across all supported\\\\nchannels.\\\\n10. Design a Logging and Monitoring\\\\nSystem\\\\nFunctional Requirements:\\\\nCollect logs from various sources such as\\\\napplications, servers, databases, and\\\\nmicroservices.\\\\nSupport for multiple log formats (e.g., JSON,\\\\nplaintext, XML).\\\\nArchive old logs to cost-effective storage (e.g.,\\\\ncloud-based cold storage).\\\\nProvide powerful querying capabilities to filter\\\\nand search logs based on time range, log level,\\\\nsource, and other attributes.\\\\nSet up alerts based on specific log patterns,\\\\nthresholds, or anomalies.\\\\nNon-Functional Requirements:\\\\nScalability: The system should scale horizontally\\\\nto handle increasing volumes of logs, metrics, and\\\\nmonitoring data.\\\\nLow-latency log ingestion and processing to\\\\nensure real-time monitoring.\\\\nHigh availability with minimal downtime (e.g.,\\\\n99.99% uptime) to ensure continuous monitoring.\\\\nDurability: Ensure that log data is stored with\\\\nhigh durability, with replication across multiple\\\\nnodes or data centers.\\", \\"page_count\\": 75, \\"ocr_processed\\": false}}, \\"upload_result\\": {\\"success\\": true, \\"url\\": \\"/uploads/church_docs/20250815_000604_2c3b196b.pdf\\", \\"filename\\": \\"20250815_000604_2c3b196b.pdf\\", \\"size\\": 2579995, \\"content_type\\": \\"application/pdf\\"}}, \\"internal_notes\\": \\"let me connect\\"}"	\N	0.00
20	Church for frank ting	\N	\N			churchadmin5@manna.com	not_submitted	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	f	pending_kyc	\N	2025-08-18 18:05:49.218921-05	2025-08-18 18:05:49.218924-05				\N	\N	\N	\N	not_submitted	f	f	\N	\N	\N	\N	\N	\N	\N			US	\N	\N	0.00
22	Church for church admin	\N	\N			church.admin.1@manna.com	not_submitted	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	f	pending_kyc	\N	2025-08-18 18:10:37.892142-05	2025-08-18 18:10:37.892145-05				\N	\N	\N	\N	not_submitted	f	f	\N	\N	\N	\N	\N	\N	\N			US	\N	\N	0.00
19	Church 2	12-2456789	https://church.manna.com	21324323432		churchadmin@manna.com	approved	2025-08-18 17:03:48.384366-05	2025-08-18 17:17:15.358536-05	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	t	t	t	t	t	t	\N	f	active	acct_1Rxb9gDFkJiuVPZh	2025-08-18 11:29:11.86363-05	2025-08-18 17:52:11.911923-05				\N	\N	\N	\N	ACTIVE	f	f	\N	\N	\N	"{\\"articles_of_incorporation\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T22:17:15.358712+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"sdfafdsa\\"}, \\"irs_letter\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T22:17:15.358724+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"sdfafdsa\\"}, \\"bank_statement\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T22:17:15.358728+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"sdfafdsa\\"}, \\"board_resolution\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T22:17:15.358731+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"sdfafdsa\\"}}"	\N	\N	church1	church1		US	"{\\"internal_notes\\": \\"sddfdsfsafsd\\"}"	Primary Business Purpose	0.00
21	Church for church admin	\N	\N			church.admin123@manna.com	not_submitted	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	f	pending_kyc	\N	2025-08-18 18:08:40.477614-05	2025-08-18 18:08:40.477617-05				\N	\N	\N	\N	not_submitted	f	f	\N	\N	\N	\N	\N	\N	\N			US	\N	\N	0.00
41	Grace Community Church	12-n7kdrq6	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor2gv4zn@gracechurch.org	pending_review	2025-08-19 10:12:06.913406-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-n7kdrq6", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorh3ma9m@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxrCoReKGAnuKFa	2025-08-19 10:12:06.914447-05	2025-08-19 10:14:50.236282-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
25	Church for church admin	12-1234567	https://manna.church.com	(555) 123 1234		church.admin1@manna.com	approved	2025-08-18 18:45:42.676963-05	2025-08-18 18:46:57.213247-05	\N	\N	\N	\N	\N	/uploads/church_docs/20250818_194546_15ce04d4.pdf	/uploads/church_docs/20250818_194546_5ad10499.pdf	/uploads/church_docs/20250818_194546_f180b732.pdf	/uploads/church_docs/20250818_194546_083913d9.pdf	\N	t	t	t	t	t	t	\N	f	active	acct_1RxckIDEd53M2caD	2025-08-18 18:43:45.619378-05	2025-08-18 18:46:57.213258-05				\N	\N	\N	\N	ACTIVE	f	f	\N	\N	\N	"{\\"articles_of_incorporation\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T23:46:57.213404+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"Welcome to our site\\"}, \\"irs_letter\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T23:46:57.213413+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"Welcome to our site\\"}, \\"bank_statement\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T23:46:57.213416+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"Welcome to our site\\"}, \\"board_resolution\\": {\\"status\\": \\"approved\\", \\"approved_at\\": \\"2025-08-18T23:46:57.213419+00:00\\", \\"approved_by\\": 3, \\"approved\\": true, \\"approval_notes\\": \\"Welcome to our site\\"}}"	\N	\N	church admin	church admin		US	{"articles_metadata": {"file_info": {"filename": "kyc doc.pdf", "content_type": "application/pdf", "size": 21220, "document_type": "articles_of_incorporation", "uploaded_at": "2025-08-18T23:45:46.638410+00:00", "file_hash": "a1ed7e3773b5cc177120c1b67e7167363515a504d3e1f891324856021c62d934", "metadata": {"document_type": "articles_of_incorporation", "processing_timestamp": "2025-08-18T23:45:46.636775+00:00", "file_hash": "a1ed7e3773b5cc177120c1b67e7167363515a504d3e1f891324856021c62d934", "extracted_text": "Kycdocsinhere", "page_count": 1, "ocr_processed": false}}, "processing_result": {"metadata": {"document_type": "articles_of_incorporation", "processing_timestamp": "2025-08-18T23:45:46.636775+00:00", "file_hash": "a1ed7e3773b5cc177120c1b67e7167363515a504d3e1f891324856021c62d934", "extracted_text": "Kycdocsinhere", "page_count": 1, "ocr_processed": false}}, "upload_result": {"success": true, "url": "/uploads/church_docs/20250818_194546_15ce04d4.pdf", "filename": "20250818_194546_15ce04d4.pdf", "size": 21220, "content_type": "application/pdf"}}}	Primary Purpose	0.00
42	Grace Community Church	12-o0wf10q	https://gracechurch.org	(555) 123-4567	123 Main Street	pastordiyo1d@gracechurch.org	pending_review	2025-08-19 10:46:00.277266-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-o0wf10q", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorykdfaz@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1RxrjcDVFoLTQJMn	2025-08-19 10:46:00.277795-05	2025-08-19 10:46:08.090316-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	{"alternatives": [], "current_deadline": null, "currently_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "disabled_reason": "requirements.past_due", "errors": [], "eventually_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "past_due": ["external_account", "tos_acceptance.date", "tos_acceptance.ip"], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
26	Grace Community Church	12-3456789	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor@gracechurch.org	pending_review	2025-08-19 06:18:01.100648-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-3456789", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": true, "sanctions_compliance": true, "no_fictitious_entity": true, "background_check_consent": true, "beneficial_ownership": true, "accuracy_certification": true}}	\N	\N	\N	\N	\N	t	t	t	t	t	t	\N	t	pending_kyc	acct_1RxnYHDuhW15VvEQ	2025-08-19 06:18:01.102983-05	2025-08-19 06:18:05.581053-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	\N	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
27	Test Church	12-0f301e7	\N	555-123-4567	123 Test St	test05777ac7@example.com	pending_review	2025-08-19 06:29:21.989949-05	\N	\N	\N	\N	\N	{"church_details": {}, "control_persons": [], "attestations": {}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1RxnjGRVzWKJUmF7	2025-08-19 06:29:21.991974-05	2025-08-19 06:29:26.2402-05	Test City	TX	\N	\N	\N	\N	\N	KYC_IN_REVIEW	f	f	\N	\N	\N	\N	\N	\N	Test Church Inc.	123 Test St	\N	US	\N		0.00
28	Grace Community Church	23-8qf7k9l	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorc7s4k7@gracechurch.org	pending_review	2025-08-19 06:49:02.599439-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "23-8qf7k9l", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastormii9m3@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1Rxo2JD10P6ynz2Z	2025-08-19 06:49:02.601271-05	2025-08-19 06:49:06.90626-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	\N	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
29	Grace Community Church	12-sufyrj6	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorarr9ef@gracechurch.org	pending_review	2025-08-19 06:52:49.074732-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-sufyrj6", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorlmbr63@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1Rxo5xRdXbDaMq3e	2025-08-19 06:52:49.075307-05	2025-08-19 06:52:52.959392-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	\N	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
30	Grace Community Church	12-eoj8kkq	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorpp2dmt@gracechurch.org	pending_review	2025-08-19 07:05:12.33149-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-eoj8kkq", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor7ib3vg@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxoHxDR6Y0FDSbg	2025-08-19 07:05:12.334041-05	2025-08-19 07:08:07.151184-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["individual.dob.day", "individual.dob.month", "individual.dob.year", "individual.ssn_last_4"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
49	First Test Church	12-ure3b5m	https://gracechurch.org	(555) 123-4567	123 Main Street	doingcode333@gmail.com	pending_review	2025-08-25 13:47:34.961453-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-ure3b5m", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorb2dx9e@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "TX", "postal_code": "62701"}, "gov_id": {"type": "state_id", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": true, "sanctions_compliance": true, "no_fictitious_entity": true, "background_check_consent": true, "beneficial_ownership": true, "accuracy_certification": true}}	\N	\N	\N	\N	\N	t	t	t	t	t	t	\N	t	active	acct_1S05QbDUpgq6dyy5	2025-08-25 13:47:34.962462-05	2025-08-25 13:49:21.550426-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
31	Grace Community Church	12-mbr9e57	https://gracechurch.org	(555) 123-4567	123 Main Street	pastorgf3li8@gracechurch.org	pending_review	2025-08-19 07:14:41.198881-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-mbr9e57", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorh1zpjq@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	pending_kyc	acct_1RxoR7DJNs80NfbT	2025-08-19 07:14:41.200461-05	2025-08-19 07:14:45.509236-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	KYC_IN_REVIEW	f	f	\N	\N	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
43	Grace Community Church	12-5r643h1	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor12knwg@gracechurch.org	pending_review	2025-08-19 10:56:20.225177-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-5r643h1", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorwn5kxr@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxrtcDnvrNcA6dm	2025-08-19 10:56:20.225995-05	2025-08-19 10:58:26.097926-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
44	Grace Community Church	12-0y5bk4r	https://gracechurch.org	(555) 123-4567	123 Main Street	pastor6a3l7f@gracechurch.org	pending_review	2025-08-19 11:05:03.336912-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-0y5bk4r", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastor4ki62l@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1Rxs23DS4ruERAbs	2025-08-19 11:05:03.337449-05	2025-08-19 11:06:48.458808-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
32	Grace Community Church	12-m384qs3	https://gracechurch.org	(555) 123-4567	123 Main Street	pastordmb9vi@gracechurch.org	pending_review	2025-08-19 07:16:33.086298-05	\N	\N	\N	\N	\N	{"church_details": {"legal_name": "Grace Community Church Inc.", "ein": "12-m384qs3", "website": "https://gracechurch.org", "phone": "(555) 123-4567", "formation_date": "2010-01-15", "formation_state": "IL", "business_purpose": "Religious organization focused on community worship and outreach."}, "control_persons": [{"id": 1, "first_name": "John", "last_name": "Smith", "title": "Senior Pastor / Primary Contact", "is_primary": true, "date_of_birth": "1980-05-15", "ssn_full": "123-45-6789", "phone": "(555) 123-4567", "email": "pastorl4aso5@gracechurch.org", "address": {"line1": "123 Main Street", "city": "Springfield", "state": "IL", "postal_code": "62701"}, "gov_id": {"type": "Driver's License", "number": "IL123456789", "front_url": null, "back_url": null}}], "financials": {"annual_revenue_range": "$500,000 - $1,000,000", "primary_funding_sources": "Tithes, offerings, and donations", "expected_manna_volume": "$5,000 - $10,000 monthly"}, "documents": {"articles_of_incorporation": null, "tax_exempt_determination": null, "bank_statement": null, "board_resolution": null, "bylaws": null}, "attestations": {"tax_exempt_status": false, "sanctions_compliance": false, "no_fictitious_entity": false, "background_check_consent": false, "beneficial_ownership": false, "accuracy_certification": false}}	\N	\N	\N	\N	\N	f	f	f	f	f	f	\N	t	active	acct_1RxoSvDWI38WTzTH	2025-08-19 07:16:33.087278-05	2025-08-19 07:19:09.813743-05	Springfield	IL	\N	\N	Dr. John Smith	\N	\N	ACTIVE	t	t	\N	{"alternatives": [], "current_deadline": null, "currently_due": [], "disabled_reason": null, "errors": [], "eventually_due": ["company.tax_id"], "past_due": [], "pending_verification": []}	\N	\N	\N	\N	Grace Community Church Inc.	123 Main Street	\N	US	\N	Religious organization focused on community worship and outreach.	0.00
\.


--
-- TOC entry 5392 (class 0 OID 68861)
-- Dependencies: 253
-- Data for Name: consents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.consents (id, user_id, version, accepted_at, ip, user_agent, text_snapshot) FROM stdin;
32	105	1.0	2025-08-21 22:37:44.477846-05	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	{'transactionRead': True, 'charging': True, 'dataUsage': True}
33	106	1.0	2025-08-21 22:40:29.081302-05	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	{'transactionRead': True, 'charging': True, 'dataUsage': True}
34	96	1.0	2025-08-21 22:45:31.302506-05	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	{'transactionRead': True, 'charging': True, 'dataUsage': True}
35	110	1.0	2025-08-22 11:39:04.458062-05	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	{'transactionRead': True, 'charging': True, 'dataUsage': True}
39	119	1.0	2025-08-25 14:04:54.575025-05	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	{'transactionRead': True, 'charging': True, 'dataUsage': True}
40	123	1.0	2025-08-25 15:03:13.068552-05	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36	{'transactionRead': True, 'charging': True, 'dataUsage': True}
\.


--
-- TOC entry 5380 (class 0 OID 60308)
-- Dependencies: 241
-- Data for Name: donation_batches; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.donation_batches (id, user_id, total_amount, processing_fees, multiplier_applied, status, created_at, executed_at, church_id, stripe_charge_id, payout_status, payout_date, retry_attempts, last_retry_at, batch_type, roundup_count, collection_date, stripe_payment_intent_id) FROM stdin;
\.


--
-- TOC entry 5382 (class 0 OID 60328)
-- Dependencies: 243
-- Data for Name: donation_preferences; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.donation_preferences (id, user_id, frequency, multiplier, church_id, pause, cover_processing_fees, created_at, updated_at, roundups_enabled, minimum_roundup, monthly_cap, exclude_categories, target_church_id) FROM stdin;
7	110	biweekly	1x	\N	f	f	2025-08-22 11:40:11.719823-05	2025-08-22 11:40:14.852049-05	t	0.01	\N	\N	\N
8	113	biweekly	1x	\N	f	f	2025-08-22 20:57:59.733454-05	2025-08-22 20:58:03.469764-05	t	0.01	\N	\N	\N
11	119	biweekly	2x	\N	t	t	2025-08-25 13:56:52.605668-05	2025-08-25 14:07:52.53248-05	t	0.01	\N	\N	\N
12	123	biweekly	1x	\N	t	f	2025-08-25 15:03:06.239596-05	2025-08-25 15:05:18.20551-05	t	0.01	\N	\N	\N
\.


--
-- TOC entry 5384 (class 0 OID 60366)
-- Dependencies: 245
-- Data for Name: donation_schedules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.donation_schedules (id, user_id, access_token, amount, day_of_week, recipient_id, status, next_run, created_at) FROM stdin;
\.


--
-- TOC entry 5412 (class 0 OID 69174)
-- Dependencies: 273
-- Data for Name: donor_payouts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.donor_payouts (id, user_id, church_id, stripe_charge_id, amount_collected, fees_covered_by_donor, net_amount, collection_period_start, collection_period_end, transaction_count, roundup_multiplier_applied, monthly_cap_applied, status, created_at, processed_at) FROM stdin;
\.


--
-- TOC entry 5404 (class 0 OID 69069)
-- Dependencies: 265
-- Data for Name: impact_stories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.impact_stories (id, church_id, title, description, amount_used, category, status, image_url, published_date, people_impacted, events_held, items_purchased, is_active, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5402 (class 0 OID 69052)
-- Dependencies: 263
-- Data for Name: metrics; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.metrics (id, metric_name, metric_key, metric_value, metric_unit, metric_type, metric_category, scope_id, scope_type, period_start, period_end, context_data, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5396 (class 0 OID 68918)
-- Dependencies: 257
-- Data for Name: payment_methods; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payment_methods (id, user_id, stripe_payment_method_id, type, status, is_default, card_brand, card_last4, card_exp_month, card_exp_year, bank_name, bank_account_type, bank_account_last4, wallet_type, payment_metadata, created_at, updated_at) FROM stdin;
5	105	pm_1Rylp6RhISr2egLpDIAkcZcL	CARD	PENDING	t	visa	4242	4	2026	\N	\N	\N	\N	\N	2025-08-21 22:39:29.645737-05	\N
6	106	pm_1RylslRhISr2egLpoFP7zaRe	CARD	PENDING	t	visa	4242	12	2032	\N	\N	\N	\N	\N	2025-08-21 22:43:17.359071-05	\N
7	96	pm_1RylweRhISr2egLpq4NSbgV7	CARD	PENDING	t	visa	4242	12	2034	\N	\N	\N	\N	\N	2025-08-21 22:47:17.644782-05	\N
11	110	pm_1Ryy0aRhISr2egLpxZjbUjjj	ACH	PENDING	t	\N	\N	\N	\N	STRIPE TEST BANK	checking	6789	\N	\N	2025-08-22 11:40:07.235422-05	\N
12	113	pm_1Rz6iHRhISr2egLpo9aMSNdS	ACH	VERIFIED	t	\N	\N	\N	\N	STRIPE TEST BANK	checking	6789	\N	\N	2025-08-22 20:57:50.8174-05	2025-08-22 20:57:57.335368-05
15	119	pm_1S05j3RhISr2egLpn7HnsW5L	ACH	VERIFIED	t	\N	\N	\N	\N	STRIPE TEST BANK	checking	6789	\N	\N	2025-08-25 14:06:41.115645-05	2025-08-25 14:06:44.393333-05
16	123	pm_1S06ddRhISr2egLppg4tDEP3	ACH	VERIFIED	t	\N	\N	\N	\N	STRIPE TEST BANK	checking	6789	\N	\N	2025-08-25 15:05:08.478221-05	2025-08-25 15:05:11.962008-05
\.


--
-- TOC entry 5416 (class 0 OID 69223)
-- Dependencies: 277
-- Data for Name: payout_allocations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payout_allocations (id, donor_payout_id, church_payout_id, allocated_amount, created_at) FROM stdin;
\.


--
-- TOC entry 5366 (class 0 OID 60149)
-- Dependencies: 227
-- Data for Name: payouts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payouts (id, church_id, amount, currency, status, stripe_transfer_id, stripe_account_id, period_start, period_end, processed_at, failed_at, failure_reason, description, payout_metadata, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5406 (class 0 OID 69102)
-- Dependencies: 267
-- Data for Name: plaid_accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.plaid_accounts (id, user_id, plaid_item_id, plaid_access_token_encrypted, account_id, account_name, account_mask, account_type, institution_name, is_active, created_at, updated_at, last_synced) FROM stdin;
\.


--
-- TOC entry 5394 (class 0 OID 68877)
-- Dependencies: 255
-- Data for Name: plaid_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.plaid_items (id, user_id, item_id, access_token, status, created_at) FROM stdin;
19	105	ZavxP8aNDXIz9W85k1PlH7nDrPxMrzCg98W4V	access-sandbox-1ce030d2-8f57-428c-94b9-21bcbc2b0166	active	2025-08-21 22:38:24.14033-05
20	106	AXXB55Aodgi146DGG4WosnB5qXmnagF1eXgAW	access-sandbox-8f9b0e78-461c-47c4-b361-65095d0e0295	active	2025-08-21 22:41:03.951083-05
21	96	j98zdlowj6iGnBKmzDd1Ur1lvALanwf1wNkMr	access-sandbox-e9479833-b26f-46f3-bde9-74c3865424f2	active	2025-08-21 22:46:09.490116-05
22	110	rnJjWZjL94FJVXLBKqg6Ij83jdbeG9FlBm7yZ	access-sandbox-94179747-a696-4c78-a26a-cb5b296579d2	active	2025-08-22 11:39:47.941805-05
23	113	X4qDoLBpd7co6QmZzJN7HvnnJ4nz9Bidam8oy	access-sandbox-29c8135a-52c8-4f06-b116-b6774be9c343	active	2025-08-22 20:57:23.605546-05
26	119	BGoozg1MQXHEdNmNm7goigkma6wlWQhwLd5ZE	access-sandbox-302d9741-1758-421c-b658-88f1a8065090	active	2025-08-25 14:05:38.535558-05
27	123	WdpLzyQPmbFJ7R1P3JNnI76G5VqxN6slxz1RB	access-sandbox-df2cffeb-0fd6-40b5-9d5a-c9d634c0eb8e	active	2025-08-25 15:04:06.637718-05
\.


--
-- TOC entry 5386 (class 0 OID 60384)
-- Dependencies: 247
-- Data for Name: referral_commissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.referral_commissions (id, referral_id, church_id, amount, commission_rate, base_amount, status, paid_at, payout_id, created_at, updated_at, church_referral_id, church_payout_id, commission_amount, period_start, period_end) FROM stdin;
\.


--
-- TOC entry 5368 (class 0 OID 60167)
-- Dependencies: 229
-- Data for Name: referrals; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.referrals (id, referring_church_id, referred_church_id, referral_code, commission_rate, commission_amount, status, is_active, created_at, updated_at, activated_at, completed_at) FROM stdin;
13	25	25	CHURCH_25_1C5C8379	0.1000	0.00	pending	t	2025-08-18 18:44:08.020281-05	\N	\N	\N
\.


--
-- TOC entry 5388 (class 0 OID 60408)
-- Dependencies: 249
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.refresh_tokens (id, user_id, token, expires_at, created_at, last_used, is_active, device_info, ip_address, user_agent, rotation_count, parent_token_id) FROM stdin;
462	119	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTY3NTMwMDl9.jPkdNsWNwVaRBewZq0iwlZKdas_eUcTyqDmoxnZkpxA	2025-09-24 13:56:49.61317-05	2025-08-25 13:56:49.613537-05	\N	t	\N	\N	\N	0	\N
\.


--
-- TOC entry 5410 (class 0 OID 69148)
-- Dependencies: 271
-- Data for Name: roundup_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roundup_settings (id, user_id, church_id, collection_frequency, roundup_multiplier, monthly_cap, cover_processing_fees, is_active, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5398 (class 0 OID 68992)
-- Dependencies: 259
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transactions (id, type, category, status, amount_cents, currency, user_id, church_id, payment_method_id, stripe_payment_intent_id, stripe_charge_id, stripe_transfer_id, roundup_period_key, roundup_multiplier, roundup_base_amount, transaction_count, batch_id, batch_type, period_start, period_end, processing_fees_cents, failure_reason, description, transaction_metadata, created_at, updated_at, processed_at, failed_at, legacy_model, legacy_id) FROM stdin;
\.


--
-- TOC entry 5390 (class 0 OID 60444)
-- Dependencies: 251
-- Data for Name: user_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_settings (id, user_id, notifications_enabled, email_notifications, sms_notifications, push_notifications, privacy_share_analytics, privacy_share_profile, created_at, updated_at, language, timezone, currency, theme) FROM stdin;
23	104	t	t	f	t	t	f	2025-08-21 22:28:16.505614-05	2025-08-21 22:28:16.505758-05	en	UTC	USD	light
24	105	t	t	f	t	t	f	2025-08-21 22:37:39.825239-05	2025-08-21 22:37:39.825354-05	en	UTC	USD	light
25	106	t	t	f	t	t	f	2025-08-21 22:40:23.902933-05	2025-08-21 22:40:23.903006-05	en	UTC	USD	light
26	96	t	t	f	t	t	f	2025-08-21 22:45:26.08998-05	2025-08-21 22:45:26.090192-05	en	UTC	USD	light
27	110	t	t	f	t	t	f	2025-08-22 11:39:00.782575-05	2025-08-22 11:39:00.782748-05	en	UTC	USD	light
\.


--
-- TOC entry 5370 (class 0 OID 60186)
-- Dependencies: 231
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, first_name, middle_name, last_name, email, phone, password, is_email_verified, is_phone_verified, is_active, role, google_id, apple_id, church_id, stripe_customer_id, profile_picture_url, created_at, updated_at, last_login, permissions, password_hash) FROM stdin;
123	Frank	\N	T	doingcode333@gmail.com	\N	\N	t	\N	t	user	115134350644849971043	\N	\N	cus_SvyY9N1TAH1oXN	\N	2025-08-25 15:03:01.639009-05	\N	\N	\N	\N
103	Benjamin	\N	Van Cauwenbergh	john.dsadoe@example.com	\N	$2b$12$hznzIefNGNKRP2D2DqgbQ.8Bp6OLE5Ls5iRy4E75l55Zl4aYucTbG	t	f	t	user	\N	\N	\N	\N	\N	2025-08-21 21:33:55.12017-05	2025-08-21 21:34:03.095926-05	\N	["user"]	\N
104	Benjamin	\N	Van Cauwenbergh	donorsda@example.com	(555) 123-4569	$2b$12$5R2PGnFpEMGq0JfJmKYxyOJ1BiWJ83IYb.SaYtLWB9E2TD41teBDG	t	f	t	user	\N	\N	\N	\N	\N	2025-08-21 22:27:36.402483-05	2025-08-21 22:28:16.468681-05	\N	["user"]	\N
110	Benjamin	\N	Van Cauwenbergh	jane.smith@example.com	+11231231231	$2b$12$NDw7Rnu7ukPdXFijSQbenOEI6gBipvQqbZ0GoXXOlk9fnr2sgl0jC	t	t	t	user	\N	\N	\N	cus_SunbIiGWb4N6RI	\N	2025-08-22 11:38:43.702911-05	2025-08-22 11:39:55.889042-05	\N	["user"]	\N
105	Benjamin	\N	Van Cauwenbergh	church.admin@manna.com	\N	$2b$12$FSNIict2F5.ZijIgmTwUhu1EndJLJD1KqQFrAQ4wcrfWamHaExALW	t	f	t	user	\N	\N	\N	cus_Sub035CsEqrqHg	\N	2025-08-21 22:37:13.101095-05	2025-08-21 22:38:59.729416-05	\N	["user"]	\N
111	Dr.	\N	John	pastorftzr7b@gracechurch.org	\N	$2b$12$UfYYwqpsAqdLTl7t4wj./ekJhhtyUbmXrqwkKJsbC/ZWMttcSiiiu	f	f	t	church_admin	\N	\N	46	\N	\N	2025-08-22 11:42:14.109326-05	2025-08-22 11:42:14.10933-05	\N	["church_management", "user_management", "analytics"]	\N
106	Benjamin	\N	Van Cauwenbergh	donorale@example.com	\N	$2b$12$7zpBml4BHQGDPaZvJR3/FeO5/tHlB3Y40MkNpFSd.FXXum7ZtqLf.	t	f	t	user	\N	\N	\N	cus_Sub2PuIM2eTlLe	\N	2025-08-21 22:40:11.628517-05	2025-08-21 22:41:10.005082-05	\N	["user"]	\N
112	Dr.	\N	John	benjaminvancauwenbergh86215@gmail.com	\N	$2b$12$d6lY21cbYAF/z080ItpYMOoLktXigl75wfgOWmfmunmr69MDfsqq.	f	f	t	church_admin	110535050229891577969	\N	47	\N	\N	2025-08-22 12:29:55.517234-05	2025-08-22 12:32:38.717265-05	\N	["church_management", "user_management", "analytics"]	\N
96	Benjamin	\N	Van Cauwenbergh	donor@example.com	\N	$2b$12$D8RXXCeN0YbWB11k/0UFCeF.1oio.rH5kdIWxIHVtmTJ0M0oHxcXO	t	f	t	user	\N	\N	\N	cus_Sub8VtneNvWFdY	\N	2025-08-21 20:31:43.656771-05	2025-08-21 22:46:23.351795-05	\N	["user"]	\N
95	Benjamin	\N	Van Cauwenbergh	donor.manna@example.com	\N	$2b$12$JWqg1/Esrp3q7gZIJbCZ7..Cr27EA4Sc0rfLWNo.38c31LqwkrJiS	f	f	t	user	\N	\N	\N	\N	\N	2025-08-21 20:19:17.611398-05	2025-08-21 20:19:17.6114-05	\N	["user"]	\N
97	Benjamin	\N	Van Cauwenbergh	john.doeee@example.com	\N	$2b$12$2HR0yYGt6.6.X2bgjqusJusqYjj0l6DyV8Nf5EEAtVbXPBEdR9FdS	f	f	t	user	\N	\N	\N	\N	\N	2025-08-21 20:33:17.59221-05	2025-08-21 20:33:17.592213-05	\N	["user"]	\N
98	Benjamin	\N	Van Cauwenbergh	john.doe@example.com	\N	$2b$12$vFRm7ALQda8z9qV.7GYgl.E0waQAXTvKe7UlsPI0dusI0pd/5qasy	f	f	t	user	\N	\N	\N	\N	\N	2025-08-21 20:36:51.752602-05	2025-08-21 20:36:51.752606-05	\N	["user"]	\N
99	Benjamin	\N	Van Cauwenbergh	jane.smithes@example.com	\N	$2b$12$2Mlqk5OkkEZ9uHw66pRVA.RTpBGHiYLs5IbAQvroq9g4bWvZul0yS	t	f	t	user	\N	\N	\N	\N	\N	2025-08-21 21:14:17.572202-05	2025-08-21 21:14:31.470634-05	\N	["user"]	\N
19	User	\N	3	admin@manna.com	\N	$2b$12$p/PYaVlWwOgTFD9MP9EkKunV9PNjbummsWxN74Glyae74DV2J1QUa	t	f	t	admin	\N	\N	\N	\N	\N	2025-08-15 08:32:32.050328-05	2025-08-15 08:32:32.050332-05	\N	["admin", "church_management", "user_management", "analytics"]	\N
100	Frank	\N	Ting	donor2@gmail.com	\N	$2b$12$0wmuVWGMfsxxwKlLaLCTB.qNALC5gHx4YoHCkT7SgSsIrSAHuS6Sa	t	f	t	user	\N	\N	\N	\N	\N	2025-08-21 21:16:08.777982-05	2025-08-21 21:16:22.099391-05	\N	["user"]	\N
101	Benjamin	\N	Van Cauwenbergh	church3@manna.com	\N	$2b$12$bn6/c3uq.tv5NnngN3rtA.XctHQEriXXNYyiaaXR/DyEqY7w8M4xy	t	f	t	user	\N	\N	\N	\N	\N	2025-08-21 21:17:50.873951-05	2025-08-21 21:18:03.479649-05	\N	["user"]	\N
102	Benjamin	\N	Van Cauwenbergh	john.doeds@example.com	\N	$2b$12$HhtR9IZjINrGklBN3t6CJO0OUj.PgykYP7jd3dNCKtbyCaub/3BvC	t	f	t	user	\N	\N	\N	\N	\N	2025-08-21 21:23:40.611322-05	2025-08-21 21:23:49.191462-05	\N	["user"]	\N
119	John	\N	Doe	john.example@gmail.com	\N	$2b$12$EzCR1hvsQVCG1wQj7i7F2eML6sR35uvwHPz9vg7QtcA7y1hm/CBHu	t	f	t	user	\N	\N	\N	cus_SvxdmD0UmDK112	\N	2025-08-25 13:55:16.321753-05	2025-08-25 14:05:43.366943-05	\N	\N	\N
120	Dr.	\N	John	pastorif30yt@gracechurch.org	\N	$2b$12$EhuQQj4aWf4qBxWoI2E/yeuLz4OCpdYimCid3Dpta4UDwb.KZMGUO	f	f	t	church_admin	\N	\N	50	\N	\N	2025-08-25 14:34:43.269128-05	2025-08-25 14:34:43.269131-05	\N	\N	\N
121	Dr.	\N	John	pastortxzjr1@gracechurch.org	\N	$2b$12$6lE5tKsAO/F0AsfngHWj1O1KyQ4yFTiWG8CRr9vztMV66EU8QOqqe	f	f	t	church_admin	\N	\N	51	\N	\N	2025-08-25 14:51:12.181155-05	2025-08-25 14:51:12.181158-05	\N	\N	\N
122	Dr.	\N	John	pastorsdybgm@gracechurch.org	\N	$2b$12$pMvJQdfb7QoXxHGz9ezAIenH0X07qvnCbLkatUm2tA2NJXXrXsxbC	f	f	t	church_admin	\N	\N	52	\N	\N	2025-08-25 14:58:58.280946-05	2025-08-25 14:58:58.280953-05	\N	\N	\N
115	Test	\N	Donor	testdonor@example.com	+1234567890	b55c8792d1ce458e279308835f8a97b580263503e76e1998e279703e35ad0c2e	t	f	t	user	\N	\N	47	cus_SuxDyhIPeCMfSo	\N	2025-07-01 21:36:10-05	\N	\N	\N	\N
113	Benjamin	\N	Van Cauwenbergh	test.test@manna.com	\N	$2b$12$nCKHKUv7vLD8Q4F55IGD.eb1Gq2cHiya2/AF5W5hEFBCXH5/h4IbS	t	f	t	user	\N	\N	47	cus_SuwbaupZFGngUD	\N	2025-06-22 20:55:54-05	2025-06-01 20:57:28-05	\N	\N	\N
\.


--
-- TOC entry 5454 (class 0 OID 0)
-- Dependencies: 232
-- Name: access_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.access_codes_id_seq', 28, true);


--
-- TOC entry 5455 (class 0 OID 0)
-- Dependencies: 216
-- Name: admin_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admin_users_id_seq', 4, true);


--
-- TOC entry 5456 (class 0 OID 0)
-- Dependencies: 260
-- Name: analytics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.analytics_id_seq', 1, false);


--
-- TOC entry 5457 (class 0 OID 0)
-- Dependencies: 218
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 870, true);


--
-- TOC entry 5458 (class 0 OID 0)
-- Dependencies: 234
-- Name: bank_accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bank_accounts_id_seq', 13, true);


--
-- TOC entry 5459 (class 0 OID 0)
-- Dependencies: 236
-- Name: beneficial_owners_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.beneficial_owners_id_seq', 27, true);


--
-- TOC entry 5460 (class 0 OID 0)
-- Dependencies: 238
-- Name: church_admins_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.church_admins_id_seq', 51, true);


--
-- TOC entry 5461 (class 0 OID 0)
-- Dependencies: 268
-- Name: church_memberships_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.church_memberships_id_seq', 1, false);


--
-- TOC entry 5462 (class 0 OID 0)
-- Dependencies: 222
-- Name: church_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.church_messages_id_seq', 13, true);


--
-- TOC entry 5463 (class 0 OID 0)
-- Dependencies: 274
-- Name: church_payouts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.church_payouts_id_seq', 1, false);


--
-- TOC entry 5464 (class 0 OID 0)
-- Dependencies: 224
-- Name: church_referrals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.church_referrals_id_seq', 1, false);


--
-- TOC entry 5465 (class 0 OID 0)
-- Dependencies: 220
-- Name: churches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.churches_id_seq', 52, true);


--
-- TOC entry 5466 (class 0 OID 0)
-- Dependencies: 252
-- Name: consents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.consents_id_seq', 40, true);


--
-- TOC entry 5467 (class 0 OID 0)
-- Dependencies: 240
-- Name: donation_batches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.donation_batches_id_seq', 1, false);


--
-- TOC entry 5468 (class 0 OID 0)
-- Dependencies: 242
-- Name: donation_preferences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.donation_preferences_id_seq', 12, true);


--
-- TOC entry 5469 (class 0 OID 0)
-- Dependencies: 244
-- Name: donation_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.donation_schedules_id_seq', 1, false);


--
-- TOC entry 5470 (class 0 OID 0)
-- Dependencies: 272
-- Name: donor_payouts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.donor_payouts_id_seq', 1, false);


--
-- TOC entry 5471 (class 0 OID 0)
-- Dependencies: 264
-- Name: impact_stories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.impact_stories_id_seq', 3, true);


--
-- TOC entry 5472 (class 0 OID 0)
-- Dependencies: 262
-- Name: metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.metrics_id_seq', 1, false);


--
-- TOC entry 5473 (class 0 OID 0)
-- Dependencies: 256
-- Name: payment_methods_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payment_methods_id_seq', 16, true);


--
-- TOC entry 5474 (class 0 OID 0)
-- Dependencies: 276
-- Name: payout_allocations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payout_allocations_id_seq', 1, false);


--
-- TOC entry 5475 (class 0 OID 0)
-- Dependencies: 226
-- Name: payouts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payouts_id_seq', 7, true);


--
-- TOC entry 5476 (class 0 OID 0)
-- Dependencies: 266
-- Name: plaid_accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.plaid_accounts_id_seq', 1, false);


--
-- TOC entry 5477 (class 0 OID 0)
-- Dependencies: 254
-- Name: plaid_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.plaid_items_id_seq', 27, true);


--
-- TOC entry 5478 (class 0 OID 0)
-- Dependencies: 246
-- Name: referral_commissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.referral_commissions_id_seq', 1, false);


--
-- TOC entry 5479 (class 0 OID 0)
-- Dependencies: 228
-- Name: referrals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.referrals_id_seq', 13, true);


--
-- TOC entry 5480 (class 0 OID 0)
-- Dependencies: 248
-- Name: refresh_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.refresh_tokens_id_seq', 462, true);


--
-- TOC entry 5481 (class 0 OID 0)
-- Dependencies: 270
-- Name: roundup_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roundup_settings_id_seq', 1, false);


--
-- TOC entry 5482 (class 0 OID 0)
-- Dependencies: 258
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transactions_id_seq', 1, false);


--
-- TOC entry 5483 (class 0 OID 0)
-- Dependencies: 250
-- Name: user_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_settings_id_seq', 30, true);


--
-- TOC entry 5484 (class 0 OID 0)
-- Dependencies: 230
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 123, true);


--
-- TOC entry 5060 (class 2606 OID 60214)
-- Name: access_codes access_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.access_codes
    ADD CONSTRAINT access_codes_pkey PRIMARY KEY (id);


--
-- TOC entry 5022 (class 2606 OID 60018)
-- Name: admin_users admin_users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT admin_users_email_key UNIQUE (email);


--
-- TOC entry 5024 (class 2606 OID 60016)
-- Name: admin_users admin_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT admin_users_pkey PRIMARY KEY (id);


--
-- TOC entry 5020 (class 2606 OID 60007)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 5123 (class 2606 OID 69050)
-- Name: analytics analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analytics
    ADD CONSTRAINT analytics_pkey PRIMARY KEY (id);


--
-- TOC entry 5027 (class 2606 OID 60028)
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 5063 (class 2606 OID 60229)
-- Name: bank_accounts bank_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank_accounts
    ADD CONSTRAINT bank_accounts_pkey PRIMARY KEY (id);


--
-- TOC entry 5069 (class 2606 OID 60245)
-- Name: beneficial_owners beneficial_owners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.beneficial_owners
    ADD CONSTRAINT beneficial_owners_pkey PRIMARY KEY (id);


--
-- TOC entry 5072 (class 2606 OID 60265)
-- Name: church_admins church_admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_admins
    ADD CONSTRAINT church_admins_pkey PRIMARY KEY (id);


--
-- TOC entry 5074 (class 2606 OID 69096)
-- Name: church_admins church_admins_stripe_identity_session_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_admins
    ADD CONSTRAINT church_admins_stripe_identity_session_id_key UNIQUE (stripe_identity_session_id);


--
-- TOC entry 5139 (class 2606 OID 69133)
-- Name: church_memberships church_memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_memberships
    ADD CONSTRAINT church_memberships_pkey PRIMARY KEY (id);


--
-- TOC entry 5037 (class 2606 OID 60106)
-- Name: church_messages church_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_messages
    ADD CONSTRAINT church_messages_pkey PRIMARY KEY (id);


--
-- TOC entry 5157 (class 2606 OID 69211)
-- Name: church_payouts church_payouts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_payouts
    ADD CONSTRAINT church_payouts_pkey PRIMARY KEY (id);


--
-- TOC entry 5159 (class 2606 OID 69213)
-- Name: church_payouts church_payouts_stripe_transfer_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_payouts
    ADD CONSTRAINT church_payouts_stripe_transfer_id_key UNIQUE (stripe_transfer_id);


--
-- TOC entry 5040 (class 2606 OID 60121)
-- Name: church_referrals church_referrals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_referrals
    ADD CONSTRAINT church_referrals_pkey PRIMARY KEY (id);


--
-- TOC entry 5030 (class 2606 OID 60050)
-- Name: churches churches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.churches
    ADD CONSTRAINT churches_pkey PRIMARY KEY (id);


--
-- TOC entry 5032 (class 2606 OID 60054)
-- Name: churches churches_referral_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.churches
    ADD CONSTRAINT churches_referral_code_key UNIQUE (referral_code);


--
-- TOC entry 5034 (class 2606 OID 60056)
-- Name: churches churches_stripe_account_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.churches
    ADD CONSTRAINT churches_stripe_account_id_key UNIQUE (stripe_account_id);


--
-- TOC entry 5107 (class 2606 OID 68869)
-- Name: consents consents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consents
    ADD CONSTRAINT consents_pkey PRIMARY KEY (id);


--
-- TOC entry 5080 (class 2606 OID 60315)
-- Name: donation_batches donation_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_batches
    ADD CONSTRAINT donation_batches_pkey PRIMARY KEY (id);


--
-- TOC entry 5083 (class 2606 OID 68783)
-- Name: donation_preferences donation_preferences_church_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_preferences
    ADD CONSTRAINT donation_preferences_church_id_key UNIQUE (church_id);


--
-- TOC entry 5085 (class 2606 OID 60335)
-- Name: donation_preferences donation_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_preferences
    ADD CONSTRAINT donation_preferences_pkey PRIMARY KEY (id);


--
-- TOC entry 5087 (class 2606 OID 60337)
-- Name: donation_preferences donation_preferences_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_preferences
    ADD CONSTRAINT donation_preferences_user_id_key UNIQUE (user_id);


--
-- TOC entry 5090 (class 2606 OID 60375)
-- Name: donation_schedules donation_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_schedules
    ADD CONSTRAINT donation_schedules_pkey PRIMARY KEY (id);


--
-- TOC entry 5149 (class 2606 OID 69183)
-- Name: donor_payouts donor_payouts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donor_payouts
    ADD CONSTRAINT donor_payouts_pkey PRIMARY KEY (id);


--
-- TOC entry 5151 (class 2606 OID 69185)
-- Name: donor_payouts donor_payouts_stripe_charge_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donor_payouts
    ADD CONSTRAINT donor_payouts_stripe_charge_id_key UNIQUE (stripe_charge_id);


--
-- TOC entry 5129 (class 2606 OID 69077)
-- Name: impact_stories impact_stories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_stories
    ADD CONSTRAINT impact_stories_pkey PRIMARY KEY (id);


--
-- TOC entry 5125 (class 2606 OID 69063)
-- Name: metrics metrics_metric_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metrics
    ADD CONSTRAINT metrics_metric_key_key UNIQUE (metric_key);


--
-- TOC entry 5127 (class 2606 OID 69061)
-- Name: metrics metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.metrics
    ADD CONSTRAINT metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 5115 (class 2606 OID 68926)
-- Name: payment_methods payment_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_pkey PRIMARY KEY (id);


--
-- TOC entry 5117 (class 2606 OID 68928)
-- Name: payment_methods payment_methods_stripe_payment_method_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_stripe_payment_method_id_key UNIQUE (stripe_payment_method_id);


--
-- TOC entry 5166 (class 2606 OID 69229)
-- Name: payout_allocations payout_allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payout_allocations
    ADD CONSTRAINT payout_allocations_pkey PRIMARY KEY (id);


--
-- TOC entry 5044 (class 2606 OID 60157)
-- Name: payouts payouts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payouts
    ADD CONSTRAINT payouts_pkey PRIMARY KEY (id);


--
-- TOC entry 5046 (class 2606 OID 60159)
-- Name: payouts payouts_stripe_transfer_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payouts
    ADD CONSTRAINT payouts_stripe_transfer_id_key UNIQUE (stripe_transfer_id);


--
-- TOC entry 5135 (class 2606 OID 69112)
-- Name: plaid_accounts plaid_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plaid_accounts
    ADD CONSTRAINT plaid_accounts_pkey PRIMARY KEY (id);


--
-- TOC entry 5137 (class 2606 OID 69114)
-- Name: plaid_accounts plaid_accounts_plaid_item_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plaid_accounts
    ADD CONSTRAINT plaid_accounts_plaid_item_id_key UNIQUE (plaid_item_id);


--
-- TOC entry 5112 (class 2606 OID 68885)
-- Name: plaid_items plaid_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plaid_items
    ADD CONSTRAINT plaid_items_pkey PRIMARY KEY (id);


--
-- TOC entry 5095 (class 2606 OID 60390)
-- Name: referral_commissions referral_commissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referral_commissions
    ADD CONSTRAINT referral_commissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5049 (class 2606 OID 60173)
-- Name: referrals referrals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_pkey PRIMARY KEY (id);


--
-- TOC entry 5098 (class 2606 OID 60415)
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- TOC entry 5100 (class 2606 OID 60417)
-- Name: refresh_tokens refresh_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_key UNIQUE (token);


--
-- TOC entry 5147 (class 2606 OID 69159)
-- Name: roundup_settings roundup_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roundup_settings
    ADD CONSTRAINT roundup_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 5119 (class 2606 OID 69004)
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 5121 (class 2606 OID 69006)
-- Name: transactions transactions_stripe_payment_intent_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_stripe_payment_intent_id_key UNIQUE (stripe_payment_intent_id);


--
-- TOC entry 5103 (class 2606 OID 60450)
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 5105 (class 2606 OID 60452)
-- Name: user_settings user_settings_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_key UNIQUE (user_id);


--
-- TOC entry 5056 (class 2606 OID 60193)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 5058 (class 2606 OID 60195)
-- Name: users users_stripe_customer_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_stripe_customer_id_key UNIQUE (stripe_customer_id);


--
-- TOC entry 5064 (class 1259 OID 69093)
-- Name: idx_bank_accounts_account_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bank_accounts_account_id ON public.bank_accounts USING btree (account_id);


--
-- TOC entry 5065 (class 1259 OID 69094)
-- Name: idx_bank_accounts_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bank_accounts_is_active ON public.bank_accounts USING btree (is_active);


--
-- TOC entry 5066 (class 1259 OID 69092)
-- Name: idx_bank_accounts_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bank_accounts_user_id ON public.bank_accounts USING btree (user_id);


--
-- TOC entry 5075 (class 1259 OID 69100)
-- Name: idx_church_admins_identity_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_admins_identity_date ON public.church_admins USING btree (identity_verification_date) WHERE (identity_verification_date IS NOT NULL);


--
-- TOC entry 5076 (class 1259 OID 69098)
-- Name: idx_church_admins_identity_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_admins_identity_session ON public.church_admins USING btree (stripe_identity_session_id) WHERE (stripe_identity_session_id IS NOT NULL);


--
-- TOC entry 5077 (class 1259 OID 69099)
-- Name: idx_church_admins_identity_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_admins_identity_status ON public.church_admins USING btree (identity_verification_status);


--
-- TOC entry 5140 (class 1259 OID 69145)
-- Name: idx_church_memberships_church_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_memberships_church_id ON public.church_memberships USING btree (church_id);


--
-- TOC entry 5141 (class 1259 OID 69146)
-- Name: idx_church_memberships_user_church; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_church_memberships_user_church ON public.church_memberships USING btree (user_id, church_id) WHERE (is_active = true);


--
-- TOC entry 5142 (class 1259 OID 69144)
-- Name: idx_church_memberships_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_memberships_user_id ON public.church_memberships USING btree (user_id);


--
-- TOC entry 5160 (class 1259 OID 69219)
-- Name: idx_church_payouts_church_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_payouts_church_id ON public.church_payouts USING btree (church_id);


--
-- TOC entry 5161 (class 1259 OID 69221)
-- Name: idx_church_payouts_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_payouts_status ON public.church_payouts USING btree (status);


--
-- TOC entry 5162 (class 1259 OID 69220)
-- Name: idx_church_payouts_stripe_transfer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_church_payouts_stripe_transfer_id ON public.church_payouts USING btree (stripe_transfer_id);


--
-- TOC entry 5152 (class 1259 OID 69197)
-- Name: idx_donor_payouts_church_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_donor_payouts_church_id ON public.donor_payouts USING btree (church_id);


--
-- TOC entry 5153 (class 1259 OID 69199)
-- Name: idx_donor_payouts_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_donor_payouts_status ON public.donor_payouts USING btree (status);


--
-- TOC entry 5154 (class 1259 OID 69198)
-- Name: idx_donor_payouts_stripe_charge_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_donor_payouts_stripe_charge_id ON public.donor_payouts USING btree (stripe_charge_id);


--
-- TOC entry 5155 (class 1259 OID 69196)
-- Name: idx_donor_payouts_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_donor_payouts_user_id ON public.donor_payouts USING btree (user_id);


--
-- TOC entry 5163 (class 1259 OID 69241)
-- Name: idx_payout_allocations_church_payout_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payout_allocations_church_payout_id ON public.payout_allocations USING btree (church_payout_id);


--
-- TOC entry 5164 (class 1259 OID 69240)
-- Name: idx_payout_allocations_donor_payout_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payout_allocations_donor_payout_id ON public.payout_allocations USING btree (donor_payout_id);


--
-- TOC entry 5131 (class 1259 OID 69122)
-- Name: idx_plaid_accounts_account_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plaid_accounts_account_id ON public.plaid_accounts USING btree (account_id);


--
-- TOC entry 5132 (class 1259 OID 69121)
-- Name: idx_plaid_accounts_plaid_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plaid_accounts_plaid_item_id ON public.plaid_accounts USING btree (plaid_item_id);


--
-- TOC entry 5133 (class 1259 OID 69120)
-- Name: idx_plaid_accounts_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plaid_accounts_user_id ON public.plaid_accounts USING btree (user_id);


--
-- TOC entry 5143 (class 1259 OID 69171)
-- Name: idx_roundup_settings_church_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roundup_settings_church_id ON public.roundup_settings USING btree (church_id);


--
-- TOC entry 5144 (class 1259 OID 69172)
-- Name: idx_roundup_settings_user_church; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_roundup_settings_user_church ON public.roundup_settings USING btree (user_id, church_id) WHERE (is_active = true);


--
-- TOC entry 5145 (class 1259 OID 69170)
-- Name: idx_roundup_settings_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roundup_settings_user_id ON public.roundup_settings USING btree (user_id);


--
-- TOC entry 5061 (class 1259 OID 60220)
-- Name: ix_access_codes_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_access_codes_id ON public.access_codes USING btree (id);


--
-- TOC entry 5025 (class 1259 OID 60019)
-- Name: ix_admin_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_admin_users_id ON public.admin_users USING btree (id);


--
-- TOC entry 5028 (class 1259 OID 60029)
-- Name: ix_audit_logs_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_logs_id ON public.audit_logs USING btree (id);


--
-- TOC entry 5067 (class 1259 OID 60235)
-- Name: ix_bank_accounts_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bank_accounts_id ON public.bank_accounts USING btree (id);


--
-- TOC entry 5070 (class 1259 OID 60256)
-- Name: ix_beneficial_owners_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_beneficial_owners_id ON public.beneficial_owners USING btree (id);


--
-- TOC entry 5078 (class 1259 OID 60276)
-- Name: ix_church_admins_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_church_admins_id ON public.church_admins USING btree (id);


--
-- TOC entry 5038 (class 1259 OID 60112)
-- Name: ix_church_messages_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_church_messages_id ON public.church_messages USING btree (id);


--
-- TOC entry 5041 (class 1259 OID 60132)
-- Name: ix_church_referrals_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_church_referrals_id ON public.church_referrals USING btree (id);


--
-- TOC entry 5035 (class 1259 OID 60057)
-- Name: ix_churches_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_churches_id ON public.churches USING btree (id);


--
-- TOC entry 5108 (class 1259 OID 68875)
-- Name: ix_consents_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_consents_id ON public.consents USING btree (id);


--
-- TOC entry 5081 (class 1259 OID 60326)
-- Name: ix_donation_batches_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_donation_batches_id ON public.donation_batches USING btree (id);


--
-- TOC entry 5088 (class 1259 OID 60348)
-- Name: ix_donation_preferences_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_donation_preferences_id ON public.donation_preferences USING btree (id);


--
-- TOC entry 5091 (class 1259 OID 60381)
-- Name: ix_donation_schedules_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_donation_schedules_id ON public.donation_schedules USING btree (id);


--
-- TOC entry 5092 (class 1259 OID 60382)
-- Name: ix_donation_schedules_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_donation_schedules_user_id ON public.donation_schedules USING btree (user_id);


--
-- TOC entry 5130 (class 1259 OID 69083)
-- Name: ix_impact_stories_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_impact_stories_id ON public.impact_stories USING btree (id);


--
-- TOC entry 5113 (class 1259 OID 68934)
-- Name: ix_payment_methods_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_payment_methods_id ON public.payment_methods USING btree (id);


--
-- TOC entry 5042 (class 1259 OID 60165)
-- Name: ix_payouts_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_payouts_id ON public.payouts USING btree (id);


--
-- TOC entry 5109 (class 1259 OID 68891)
-- Name: ix_plaid_items_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_plaid_items_id ON public.plaid_items USING btree (id);


--
-- TOC entry 5110 (class 1259 OID 68892)
-- Name: ix_plaid_items_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_plaid_items_item_id ON public.plaid_items USING btree (item_id);


--
-- TOC entry 5093 (class 1259 OID 60406)
-- Name: ix_referral_commissions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_referral_commissions_id ON public.referral_commissions USING btree (id);


--
-- TOC entry 5047 (class 1259 OID 60184)
-- Name: ix_referrals_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_referrals_id ON public.referrals USING btree (id);


--
-- TOC entry 5096 (class 1259 OID 60423)
-- Name: ix_refresh_tokens_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_refresh_tokens_id ON public.refresh_tokens USING btree (id);


--
-- TOC entry 5101 (class 1259 OID 60458)
-- Name: ix_user_settings_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_settings_id ON public.user_settings USING btree (id);


--
-- TOC entry 5050 (class 1259 OID 60201)
-- Name: ix_users_apple_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_apple_id ON public.users USING btree (apple_id);


--
-- TOC entry 5051 (class 1259 OID 60202)
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- TOC entry 5052 (class 1259 OID 60203)
-- Name: ix_users_google_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_google_id ON public.users USING btree (google_id);


--
-- TOC entry 5053 (class 1259 OID 60204)
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- TOC entry 5054 (class 1259 OID 60205)
-- Name: ix_users_phone; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_phone ON public.users USING btree (phone);


--
-- TOC entry 5175 (class 2606 OID 60215)
-- Name: access_codes access_codes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.access_codes
    ADD CONSTRAINT access_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5167 (class 2606 OID 60484)
-- Name: audit_logs audit_logs_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5176 (class 2606 OID 60230)
-- Name: bank_accounts bank_accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank_accounts
    ADD CONSTRAINT bank_accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5177 (class 2606 OID 60246)
-- Name: beneficial_owners beneficial_owners_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.beneficial_owners
    ADD CONSTRAINT beneficial_owners_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5178 (class 2606 OID 60251)
-- Name: beneficial_owners beneficial_owners_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.beneficial_owners
    ADD CONSTRAINT beneficial_owners_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id);


--
-- TOC entry 5179 (class 2606 OID 60266)
-- Name: church_admins church_admins_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_admins
    ADD CONSTRAINT church_admins_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5180 (class 2606 OID 60271)
-- Name: church_admins church_admins_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_admins
    ADD CONSTRAINT church_admins_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5202 (class 2606 OID 69139)
-- Name: church_memberships church_memberships_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_memberships
    ADD CONSTRAINT church_memberships_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5203 (class 2606 OID 69134)
-- Name: church_memberships church_memberships_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_memberships
    ADD CONSTRAINT church_memberships_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5168 (class 2606 OID 60107)
-- Name: church_messages church_messages_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_messages
    ADD CONSTRAINT church_messages_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5208 (class 2606 OID 69214)
-- Name: church_payouts church_payouts_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_payouts
    ADD CONSTRAINT church_payouts_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5169 (class 2606 OID 60122)
-- Name: church_referrals church_referrals_referred_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_referrals
    ADD CONSTRAINT church_referrals_referred_church_id_fkey FOREIGN KEY (referred_church_id) REFERENCES public.churches(id);


--
-- TOC entry 5170 (class 2606 OID 60127)
-- Name: church_referrals church_referrals_referring_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.church_referrals
    ADD CONSTRAINT church_referrals_referring_church_id_fkey FOREIGN KEY (referring_church_id) REFERENCES public.churches(id);


--
-- TOC entry 5194 (class 2606 OID 68870)
-- Name: consents consents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consents
    ADD CONSTRAINT consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5181 (class 2606 OID 60316)
-- Name: donation_batches donation_batches_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_batches
    ADD CONSTRAINT donation_batches_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5182 (class 2606 OID 60321)
-- Name: donation_batches donation_batches_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_batches
    ADD CONSTRAINT donation_batches_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5183 (class 2606 OID 60338)
-- Name: donation_preferences donation_preferences_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_preferences
    ADD CONSTRAINT donation_preferences_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5184 (class 2606 OID 68784)
-- Name: donation_preferences donation_preferences_target_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_preferences
    ADD CONSTRAINT donation_preferences_target_church_id_fkey FOREIGN KEY (target_church_id) REFERENCES public.churches(id);


--
-- TOC entry 5185 (class 2606 OID 60343)
-- Name: donation_preferences donation_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_preferences
    ADD CONSTRAINT donation_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5186 (class 2606 OID 60376)
-- Name: donation_schedules donation_schedules_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donation_schedules
    ADD CONSTRAINT donation_schedules_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5206 (class 2606 OID 69191)
-- Name: donor_payouts donor_payouts_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donor_payouts
    ADD CONSTRAINT donor_payouts_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5207 (class 2606 OID 69186)
-- Name: donor_payouts donor_payouts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.donor_payouts
    ADD CONSTRAINT donor_payouts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5200 (class 2606 OID 69078)
-- Name: impact_stories impact_stories_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_stories
    ADD CONSTRAINT impact_stories_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5196 (class 2606 OID 68929)
-- Name: payment_methods payment_methods_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5209 (class 2606 OID 69235)
-- Name: payout_allocations payout_allocations_church_payout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payout_allocations
    ADD CONSTRAINT payout_allocations_church_payout_id_fkey FOREIGN KEY (church_payout_id) REFERENCES public.church_payouts(id);


--
-- TOC entry 5210 (class 2606 OID 69230)
-- Name: payout_allocations payout_allocations_donor_payout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payout_allocations
    ADD CONSTRAINT payout_allocations_donor_payout_id_fkey FOREIGN KEY (donor_payout_id) REFERENCES public.donor_payouts(id);


--
-- TOC entry 5171 (class 2606 OID 60160)
-- Name: payouts payouts_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payouts
    ADD CONSTRAINT payouts_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5201 (class 2606 OID 69115)
-- Name: plaid_accounts plaid_accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plaid_accounts
    ADD CONSTRAINT plaid_accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5195 (class 2606 OID 68886)
-- Name: plaid_items plaid_items_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plaid_items
    ADD CONSTRAINT plaid_items_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5187 (class 2606 OID 60391)
-- Name: referral_commissions referral_commissions_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referral_commissions
    ADD CONSTRAINT referral_commissions_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5188 (class 2606 OID 69252)
-- Name: referral_commissions referral_commissions_church_payout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referral_commissions
    ADD CONSTRAINT referral_commissions_church_payout_id_fkey FOREIGN KEY (church_payout_id) REFERENCES public.church_payouts(id);


--
-- TOC entry 5189 (class 2606 OID 69247)
-- Name: referral_commissions referral_commissions_church_referral_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referral_commissions
    ADD CONSTRAINT referral_commissions_church_referral_id_fkey FOREIGN KEY (church_referral_id) REFERENCES public.church_referrals(id);


--
-- TOC entry 5190 (class 2606 OID 60396)
-- Name: referral_commissions referral_commissions_payout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referral_commissions
    ADD CONSTRAINT referral_commissions_payout_id_fkey FOREIGN KEY (payout_id) REFERENCES public.payouts(id);


--
-- TOC entry 5191 (class 2606 OID 60401)
-- Name: referral_commissions referral_commissions_referral_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referral_commissions
    ADD CONSTRAINT referral_commissions_referral_id_fkey FOREIGN KEY (referral_id) REFERENCES public.referrals(id);


--
-- TOC entry 5172 (class 2606 OID 60174)
-- Name: referrals referrals_referred_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referred_church_id_fkey FOREIGN KEY (referred_church_id) REFERENCES public.churches(id);


--
-- TOC entry 5173 (class 2606 OID 60179)
-- Name: referrals referrals_referring_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referring_church_id_fkey FOREIGN KEY (referring_church_id) REFERENCES public.churches(id);


--
-- TOC entry 5192 (class 2606 OID 60418)
-- Name: refresh_tokens refresh_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5204 (class 2606 OID 69165)
-- Name: roundup_settings roundup_settings_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roundup_settings
    ADD CONSTRAINT roundup_settings_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5205 (class 2606 OID 69160)
-- Name: roundup_settings roundup_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roundup_settings
    ADD CONSTRAINT roundup_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5197 (class 2606 OID 69012)
-- Name: transactions transactions_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


--
-- TOC entry 5198 (class 2606 OID 69017)
-- Name: transactions transactions_payment_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_payment_method_id_fkey FOREIGN KEY (payment_method_id) REFERENCES public.payment_methods(id);


--
-- TOC entry 5199 (class 2606 OID 69007)
-- Name: transactions transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5193 (class 2606 OID 60453)
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5174 (class 2606 OID 60196)
-- Name: users users_church_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_church_id_fkey FOREIGN KEY (church_id) REFERENCES public.churches(id);


-- Completed on 2025-08-28 22:11:30

--
-- PostgreSQL database dump complete
--

