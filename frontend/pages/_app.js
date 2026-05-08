import React from 'react'
import Head from 'next/head'

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Energy Dashboard</title>
      </Head>
      <Component {...pageProps} />

      <style jsx global>{`
        html,body,#__next { height:100%; }
        body { margin:0; background: #071019; font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; }
        * { box-sizing: border-box }
      `}</style>
    </>
  )
}
